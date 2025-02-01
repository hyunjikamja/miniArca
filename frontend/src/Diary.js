import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Diary.css'; // App.css 대신 Diary.css로 변경

function App() {
  const [diaryText, setDiaryText] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [savedEntries, setSavedEntries] = useState([]);

  // 일기 분석 요청
  const analyzeDiary = async () => {
    try {
      const response = await axios.post('http://localhost:8000/analyzeDiary', {
        content: diaryText
      });
      setAnalysisResults(response.data);
      fetchSavedEntries(); // 저장된 데이터 새로고침
    } catch (error) {
      console.error('분석 오류:', error);
    }
  };

  // 저장된 일기 데이터 가져오기
  const fetchSavedEntries = async () => {
    try {
      const response = await axios.get('http://localhost:8000/entries');
      setSavedEntries(response.data);
    } catch (error) {
      console.error('데이터 가져오기 오류:', error);
    }
  };

  // 컴포넌트 마운트 시 저장된 데이터 가져오기
  useEffect(() => {
    fetchSavedEntries();
  }, []);

  return (
    <div className="Diary"> {/* App 대신 Diary로 변경 */}
      <h1>일기 분석 시스템</h1>
      
      {/* 일기 입력 섹션 */}
      <div className="input-section">
        <textarea
          value={diaryText}
          onChange={(e) => setDiaryText(e.target.value)}
          placeholder="일기를 입력하세요..."
        />
        <button onClick={analyzeDiary}>분석하기</button>
      </div>

      {/* 분석 결과 표시 섹션 */}
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

      {/* 저장된 일기 목록 */}
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

