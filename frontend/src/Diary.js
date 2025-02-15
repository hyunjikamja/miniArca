import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import './Diary.css';

function App() {
  const [diaryText, setDiaryText] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [savedEntries, setSavedEntries] = useState([]);
  const [analysisId, setAnalysisId] = useState(null);
  const location = useLocation();

  useEffect(() => {
    if (location.state && location.state.analysisId) {
      setAnalysisId(location.state.analysisId);
    }
    fetchSavedEntries();
  }, [location]);

  const analyzeDiary = async () => {
    try {
      const response = await axios.post('http://localhost:8000/analyzeDiary', {
        content: diaryText,
        analysis_id: analysisId
      });
      setAnalysisResults(response.data);
      fetchSavedEntries();
    } catch (error) {
      console.error('분석 오류:', error);
    }
  };

  const fetchSavedEntries = async () => {
    try {
      const response = await axios.get('http://localhost:8000/entries');
      setSavedEntries(response.data);
    } catch (error) {
      console.error('데이터 가져오기 오류:', error);
    }
  };

  return (
    <div className="Diary">
      <h1>일기 분석 시스템</h1>
      
      <div className="input-section">
        <textarea
          value={diaryText}
          onChange={(e) => setDiaryText(e.target.value)}
          placeholder="일기를 입력하세요..."
        />
        <button onClick={analyzeDiary}>분석하기</button>
      </div>

      {analysisResults && (
        <div className="analysis-results">
          <h2>분석 결과</h2>
          <div>
            <h3>감정 분석</h3>
            <pre>{JSON.stringify(analysisResults.emotion_analysis, null, 2)}</pre>
            
            <h3>장소</h3>
            <pre>{JSON.stringify(analysisResults.place_extraction, null, 2)}</pre>
            
            <h3>키워드</h3>
            <pre>{JSON.stringify(analysisResults.object_keywords, null, 2)}</pre>
          </div>
        </div>
      )}

      <div className="saved-entries">
        <h2>저장된 일기 목록</h2>
        {savedEntries.map((entry, index) => (
          <div key={index} className="entry">
            <p><strong>내용:</strong> {entry.content}</p>
            <p><strong>감정 분석:</strong> {JSON.stringify(entry.emotion_analysis)}</p>
            <p><strong>장소:</strong> {JSON.stringify(entry.place_extraction)}</p>
            <p><strong>키워드:</strong> {JSON.stringify(entry.object_keywords)}</p>
            <hr />
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
