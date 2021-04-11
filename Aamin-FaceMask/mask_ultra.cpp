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
#include </usr/include/boost/asio.hpp>
#include </usr/include/boost/date_time/posix_time/posix_time.hpp>
#include </usr/include/boost/beast/core.hpp>
#include </usr/include/boost/beast/http.hpp>
#include </usr/include/boost/beast/version.hpp>
#include </usr/include/boost/asio/ip/tcp.hpp>
#include </usr/include/boost/config.hpp>




using namespace std;
using namespace paddle::lite_api;  // NOLIN
using namespace std::chrono;
using boost::asio::ip::tcp;
namespace http = boost::beast::http;
std::vector<uchar> buffer;
cv::Mat frame;





    void storeDB(const char* id, const char* type, const char* date, const char* time){

            Py_InitializeEx(0);

            PyRun_SimpleString("import sys");
            PyRun_SimpleString("if not hasattr(sys,'argv'): sys.argv = ['']");
            PyRun_SimpleString("sys.path.append('./')");
            PyObject* moduleName = PyUnicode_FromString("script");
            PyObject* pModule = PyImport_Import(moduleName);

            if (pModule == NULL) {
            printf("ERROR importing module");
            }

            PyObject* fooFunc = PyObject_GetAttrString(pModule, "stor_in_DB");

            if (fooFunc == NULL) {
                printf("ERROR getting Hello attribute");

            }
            cout << "innnnnnnnnnnnnnnnnnnnnnnnn"<< endl;
            PyObject* param1 = PyUnicode_FromFormat("%s", id);
            PyObject* param2 = PyUnicode_FromFormat("%s", type);
            PyObject* param3 = PyUnicode_FromFormat("%s", date);
            PyObject* param4 = PyUnicode_FromFormat("%s", time);
            PyObject* args = PyTuple_Pack(4, param1,param2,param3,param4);
            PyObject* result = PyObject_CallObject(fooFunc,args);


            Py_CLEAR(result);
            Py_CLEAR(args);
            Py_CLEAR(param1);
            Py_CLEAR(param2);
            Py_CLEAR(param3);
            Py_CLEAR(param4);
            Py_CLEAR(fooFunc);
            Py_CLEAR(pModule);
            Py_CLEAR(moduleName);


            Py_Finalize();



        }



    void violtion(int &countv,cv::Mat& frame){
            cv::imwrite("violation"+std::to_string(countv)+".jpeg",frame);
            time_t rawtime;
            struct tm * timeinfo;
            char date[80];
            char Time[80];

            time (&rawtime);
            timeinfo = localtime(&rawtime);

            strftime(date,sizeof(date),"%d-%m-%Y",timeinfo);
            strftime(Time,sizeof(Time),"%H:%M:%S",timeinfo);

            const char* type = "face mask";

            char V_num[5 + sizeof(char)];

            std::sprintf(V_num, "%d", countv);

            storeDB(V_num,type,date,Time);
            countv++;

        }





int main(int argc,char ** argv)

{
    std::chrono::seconds s(10);
    int countv = 1;
    cv::Mat frame1;
    bool mask = false;
    float f;
    float FPS[16];
    int i, Fcnt=0;
    int classify_w = 128;
    int classify_h = 128;
    float scale_factor = 1.f / 256;
    int FaceImgSz  = classify_w * classify_h;
    std::vector<std::chrono::seconds> times;
    std::vector<bool> locks;
    //std::vector<std::chrono::time_point> times;

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
    tcp::acceptor acceptor(io_service, tcp::endpoint(tcp::v4(), 5000));
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



    cv::VideoCapture cap(0);

    if (!cap.isOpened()) {
        cerr << "ERROR: Unable to open the camera" << endl;
        return 0;
    }
    cout << "Start grabbing, press ESC on Live window to terminate" << endl;

    while(cap.isOpened()){
            //std::chrono::time_point<std::chrono::system_clock> timer;
            //timer = std::chrono::system_clock::now();
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



        for(long unsigned int i = 0; i < face_info.size(); i++) {

            auto face = face_info[i];

            if (face_info.size() > locks.size() & face_info.size() > times.size()){
           // times.push_back(timer);
            locks.push_back(false);
            times.push_back(std::chrono::seconds (50));
            }

            if (face_info.size() < locks.size() & face_info.size() < times.size()){

            locks.pop_back();
            times.pop_back();

            }
            //enlarge 10%
            float w = (face.x2 - face.x1)/20.0;
            float h = (face.y2 - face.y1)/20.0;
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
                float* dout_c1 = input_data + FaceImgSz;
                float* dout_c2 = input_data + FaceImgSz * 2;

                for(int i=0;i<FaceImgSz;i++){
                    *(dout_c0++) = (*(dimg++) - 0.5);
                    *(dout_c1++) = (*(dimg++) - 0.5);
                    *(dout_c2++) = (*(dimg++) - 0.5);
                }

                // Classification Model Run
                Mpredictor->Run();

                auto* outptr = output_tensor1->data<float>();
                float prob = outptr[1];

                // Draw Detection and Classification Results
                bool flag_mask = prob > 0.4f;
                cv::Scalar roi_color_green;
                cv::Scalar roi_color_red;

                if(flag_mask){

                    roi_color_green = cv::Scalar(0, 255, 0);
                    locks[i] = false;
                    cv::rectangle(frame, RecClip, roi_color_green, 2);
                    mask = true;
                }
                else{

                    locks[i] = true;
                    roi_color_red = cv::Scalar(0, 0, 255);
                    cv::rectangle(frame, RecClip, roi_color_red, 2);
                    mask = false;

                }
                // Draw roi object
            if(mask == false){
                if (locks[i] == true){

                times[i]=--times[i];

                }

                //durations[i] = chrono::duration_cast <chrono::milliseconds> (times[i]).count();
                cout << "face: " <<i<< endl;
                cout << "time: " <<times.at(i).count()<< endl;
                if (times.at(i).count() == 0 ){
                  cout << "gggggggggggggggh"<< endl;
                        violtion(countv,frame);
                        times[i] = std::chrono::seconds (50);
                }

            }else{
                 times[i] = std::chrono::seconds (50);
            }




        }
}

        Tend = chrono::steady_clock::now();
        //calculate frame rate
        f = chrono::duration_cast <chrono::milliseconds> (Tend - Tbegin).count();
        if(f>0.0) FPS[((Fcnt++)&0x0F)]=1000.0/f;
        for(f=0.0, i=0;i<16;i++){ f+=FPS[i]; }
        cv::putText(frame, cv::format("FPS %0.2f", f/16),cv::Point(10,20),cv::FONT_HERSHEY_SIMPLEX,0.6, cv::Scalar(0, 0, 255));


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
