import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const PhotoCapture = () => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [capturedImage, setCapturedImage] = useState(null);
    const navigate = useNavigate();

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoRef.current.srcObject = stream;
        } catch (err) {
            console.error("카메라 시작 오류:", err);
        }
    };

    const capturePhoto = () => {
        const canvas = canvasRef.current;
        const context = canvas.getContext("2d");
        context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL("image/png");
        setCapturedImage(imageData);
    };

    const analyzePhoto = async () => {
        if (!capturedImage) return;
        try {
          const blob = await fetch(capturedImage).then((res) => res.blob());
          const formData = new FormData();
          formData.append("file", blob, "photo.png");
          const response = await axios.post("http://localhost:8000/analyzePhoto", formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          const analysisId = response.data.analysis_id;
          // 분석 요청 후 analysis_id를 포함하여 다음 페이지로 이동
          navigate("/diary", { state: { analysisId } });
        } catch (error) {
          console.error('사진 분석 요청 오류:', error);
        }
      };
      

    return (
        <div>
            <h1>사진 촬영</h1>
            <video ref={videoRef} autoPlay width={400} height={300} />
            <button onClick={startCamera}>카메라 시작</button>
            <button onClick={capturePhoto}>사진 촬영</button>
            {capturedImage && <img src={capturedImage} alt="Captured" width={400} height={300} />}
            <button onClick={analyzePhoto} disabled={!capturedImage}>
                사진 분석 후 이동
            </button>
            <canvas ref={canvasRef} width={400} height={300} style={{ display: "none" }} />
        </div>
    );
};

export default PhotoCapture;
