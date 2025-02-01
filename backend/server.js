const express = require('express');
const cors = require('cors');
const axios = require('axios');
const multer = require('multer');
const FormData = require('form-data');
const app = express();
const port = 5000;

app.use(cors());
app.use(express.json());

// Multer 설정
const upload = multer({ storage: multer.memoryStorage() });

// FastAPI 서버로 일기 분석 요청을 전달하는 미들웨어
app.post('/analyzeDiary', async (req, res) => {
  try {
    const response = await axios.post('http://localhost:8000/analyzeDiary', req.body);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// FastAPI 서버로 사진 분석 요청을 전달하는 미들웨어
app.post('/analyzePhoto', upload.single('file'), async (req, res) => {
  try {
    const formData = new FormData();
    formData.append('file', req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype
    });

    const response = await axios.post('http://localhost:8000/analyzePhoto', formData, {
      headers: {
        ...formData.getHeaders()
      }
    });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 저장된 데이터 조회 엔드포인트
app.get('/entries', async (req, res) => {
  try {
    const response = await axios.get('http://localhost:8000/entries');
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
