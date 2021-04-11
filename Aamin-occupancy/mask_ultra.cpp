// Copyright (c) 2019 PaddlePaddle Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "/usr/include/python3.7m/Python.h"
#include <ctime>
#include <cmath>
#include <memory>
#include <typeinfo>
#include <iostream>
#include <string>
#include <vector>
#include <opencv2/highgui.hpp>
#include "opencv2/imgproc.hpp"
#include "opencv2/imgcodecs.hpp"
#include "opencv2/core.hpp"
#include "/home/pi/Paddle-Lite/lite/api/paddle_api.h"  // NOLINT
#include "UltraFace.hpp"
#include <time.h>
#include <cstdlib>
#include <unistd.h>
#include <chrono>
#include </usr/include/boost/beast/core.hpp>
#include </usr/include/boost/beast/http.hpp>
#include </usr/include/boost/beast/version.hpp>
#include </usr/include/boost/asio/ip/tcp.hpp>
#include </usr/include/boost/config.hpp>
#include <thread>



using namespace std;
using namespace paddle::lite_api;  // NOLIN
using namespace std::chrono;
using boost::asio::ip::tcp;
namespace http = boost::beast::http;
std::vector<uchar> buffer;
cv::Mat frame;
int counter = 0;
int facecount = 0;



int main(int argc,char ** argv)

{

    cv::Mat frame1;
    bool detec = false;
    float h;
    int faceNo;
    float f;
    int info;
    float FPS[16];
    int i, Fcnt=0;
    int classify_w = 128;
    int classify_h = 128;
    float scale_factor = 1.f / 256;
    int FaceImgSz  = classify_w * classify_h;

    // Mask detection (second phase, when the faces are located)
    MobileConfig Mconfig;
    std::shared_ptr<PaddlePredictor> Mpredictor;
    //some timing
    chrono::steady_clock::time_point Tbegin, Tend;

    for(i=0;i<16;i++) FPS[i]=0.0;

    //load SSD face detection model and get predictor
    UltraFace ultraface("slim_320.bin","slim_320.param", 320, 240, 2, 0.7); // config model input
    //UltraFace ultraface("RFB-320.bin","RFB-320.param", 320, 240, 2, 0.7); // config model input

    //load mask detection model
    Mconfig.set_model_from_file("mask_detector_opt2.nb");
    Mpredictor = CreatePaddlePredictor<MobileConfig>(Mconfig);
    std::cout << "Load classification model succeed." << std::endl;

    // Get Input Tensor
    std::unique_ptr<Tensor> input_tensor1(std::move(Mpredictor->GetInput(0)));
    input_tensor1->Resize({1, 3, classify_h, classify_w});

    // Get Output Tensor
    std::unique_ptr<const Tensor> output_tensor1(std::move(Mpredictor->GetOutput(0)));



    boost::asio::io_context io_service;
    tcp::acceptor acceptor(io_service, tcp::endpoint(tcp::v4(), 5003));
    boost::system::error_code err;
    tcp::socket socket(io_service);
    acceptor.accept(socket);

    boost::beast::flat_buffer request_buffer;

    http::request<http::string_body> req;
    http::read(socket, request_buffer, req, err);
    if(err){
        std::cerr << "read: " << err.message() << "\n";
    }

    http::response<http::empty_body> res{http::status::ok, req.version()};
    res.set(http::field::server, BOOST_BEAST_VERSION_STRING);
    res.set(http::field::content_type, "multipart/x-mixed-replace; boundary=frame");
    res.keep_alive();
    http::response_serializer<http::empty_body> sr{res};
    http::write_header(socket, sr);



    cv::VideoCapture cap(1);

    if (!cap.isOpened()) {
        cerr << "ERROR: Unable to open the camera" << endl;
        return 0;
    }
    cout << "Start grabbing, press ESC on Live window to terminate" << endl;

    while(cap.isOpened()){
//        frame=cv::imread("Face_2.jpg");  //if you want to run just one picture need to refresh frame before class detection
        cap >> frame1;
        flip(frame1,frame,1);

        if (frame.empty()) {
            cerr << "ERROR: Unable to grab from the camera" << endl;
            break;
        }

        Tbegin = chrono::steady_clock::now();

        ncnn::Mat inmat = ncnn::Mat::from_pixels(frame.data, ncnn::Mat::PIXEL_BGR2RGB, frame.cols, frame.rows);

        //get the faces
        std::vector<FaceInfo> face_info;
        ultraface.detect(inmat, face_info);

        auto* input_data = input_tensor1->mutable_data<float>();
        info = face_info.size();

        if(info > 0){
        detec = true;
        }
        else{
        detec = false;
        }
        for(long unsigned int i = 0; i < face_info.size(); i++) {
            auto face = face_info[i];
            //enlarge 10%
            faceNo = face_info.size();
            float w = (face.x2 - face.x1)/20.0;
            h = (face.y2 - face.y1)/20.0;
            cv::Point pt1(std::max(face.x1-w,float(0.0)),std::max(face.y1-h,float(0.0)));
            cv::Point pt2(std::min(face.x2+w,float(frame.cols)),std::min(face.y2+h,float(frame.rows)));
            //RecClip is completly inside the frame
            cv::Rect  RecClip(pt1, pt2);
            cv::Mat   resized_img;
            cv::Mat   imgf;

            if(RecClip.width>0 && RecClip.height>0){
                //roi has size RecClip
                cv::Mat roi = frame(RecClip);

                //resized_img has size 128x128 (uchar)
                cv::resize(roi, resized_img, cv::Size(classify_w, classify_h), 0.f, 0.f, cv::INTER_CUBIC);

                //imgf has size 128x128 (float in range 0.0 - +1.0)
                resized_img.convertTo(imgf, CV_32FC3, scale_factor);

                //input tensor has size 128x128 (float in range -0.5 - +0.5)
                // fill tensor with mean and scale and trans layout: nhwc -> nchw, neon speed up
                //offset_nchw(n, c, h, w) = n * CHW + c * HW + h * W + w
                //offset_nhwc(n, c, h, w) = n * HWC + h * WC + w * C + c
                const float* dimg = reinterpret_cast<const float*>(imgf.data);

                float* dout_c0 = input_data;


                for(int i=0;i<FaceImgSz;i++){
                    *(dout_c0++) = (*(dimg++) - 0.5);

                }

                // Classification Model Run

                cv::rectangle(frame, RecClip, (0, 0, 255), 2);
                // Draw Detection and Classification Result

            }


        }

        if (detec == false){
        facecount =0;
        }else{


        if(h > 5){
        //cout << "face count : " <<facecount<< endl;
                    if(faceNo > facecount){


                        facecount = faceNo;
                        counter++;

                    }
                    }


                }

  Tend = chrono::steady_clock::now();

        //calculate frame rate
        f = chrono::duration_cast <chrono::milliseconds> (Tend - Tbegin).count();
        if(f>0.0) FPS[((Fcnt++)&0x0F)]=1000.0/f;
        for(f=0.0, i=0;i<16;i++){ f+=FPS[i]; }

        cv::line(frame,cv::Point(0,240),cv::Point(700,240),(100,230,144),2);
        cv::putText(frame, cv::format("hight %f", h),cv::Point(10,20),cv::FONT_HERSHEY_SIMPLEX,0.6, cv::Scalar(0, 0, 255));
        cv::putText(frame, cv::format("count %d", counter),cv::Point(20,55),cv::FONT_HERSHEY_SIMPLEX,2, cv::Scalar(0, 0, 255),3);


        cv::imencode(".jpg", frame, buffer, std::vector<int> {cv::IMWRITE_JPEG_QUALITY, 95});

        auto const size = buffer.size();

        http::response<http::vector_body<unsigned char>> res{std::piecewise_construct,
        std::make_tuple(std::move(buffer)),
        std::make_tuple(http::status::ok, req.version())};
        res.set(http::field::body, "--frame");
        res.set(http::field::server, BOOST_BEAST_VERSION_STRING);
        res.set(http::field::content_type, "image/jpeg");
        res.content_length(size);
        res.keep_alive(req.keep_alive());
        http::write(socket, res, err);
    }


  return 0;
}
