const express = require('express');
const cors = require('cors');
const axios = require('axios');
const app = express();
const port = 5000;

app.use(cors());
app.use(express.json());

// FastAPI 서버로 요청을 전달하는 미들웨어
app.post('/analyze', async (req, res) => {
  try {
    const response = await axios.post('http://localhost:8000/analyze', req.body);
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


// 배경 생성 작업 시작
app.post('/background-generation/:entryId', async (req, res) => {
  try {
    const response = await axios.post(`http://localhost:8000/background-generation/${req.params.entryId}`);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 배경 생성 작업 상태 확인
app.get('/background-generation/:taskId', async (req, res) => {
  try {
    const response = await axios.get(`http://localhost:8000/background-generation/${req.params.taskId}`);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
