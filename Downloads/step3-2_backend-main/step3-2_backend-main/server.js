const express = require('express');
const app = express();
const cors = require('cors');
const port = 3001;

app.use(express.json());
app.use(cors());

// データベースの代わりとなるメモリ上の配列
let moodRecords = [];

// 回答のスコアに基づいて色を生成するロジック
function generateColorFromAnswers(answers) {
  const totalScore = answers.reduce((sum, score) => sum + score, 0);
  const avgScore = totalScore / answers.length;
  
  let hue, saturation, lightness;

  if (avgScore >= 4.5) {
    hue = 120; // 豊かな緑
    saturation = 80;
    lightness = 70;
  } else if (avgScore >= 3.5) {
    hue = 60; // 暖かい黄色
    saturation = 70;
    lightness = 60;
  } else if (avgScore >= 2.5) {
    hue = 240; // 落ち着いた青
    saturation = 30;
    lightness = 50;
  } else {
    hue = 0; // 暖色系のくすんだ色
    saturation = 40;
    lightness = 40;
  }
  
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// === APIエンドポイント ===

// 回答を保存し、その日の色を記録する
app.post('/api/mood/save', (req, res) => {
  const { answers, userId } = req.body;
  const colorCode = generateColorFromAnswers(answers);
  const today = new Date().toISOString().split('T')[0];

  const existingIndex = moodRecords.findIndex(r => r.userId === userId && r.date === today);
  if (existingIndex !== -1) {
    moodRecords[existingIndex].colorCode = colorCode;
  } else {
    moodRecords.push({
      userId,
      date: today,
      colorCode,
      answers,
    });
  }

  console.log(`Saved mood for ${userId} on ${today} with color ${colorCode}`);
  res.status(200).json({ message: 'Mood saved', colorCode });
});

// 過去7日間の色データを取得する
app.get('/api/mood/week', (req, res) => {
  const userId = req.query.userId || 'user1';
  const today = new Date();
  
  const weeklyData = moodRecords.filter(record => {
    const recordDate = new Date(record.date);
    const diffTime = Math.abs(today - recordDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return record.userId === userId && diffDays <= 7;
  }).sort((a, b) => new Date(a.date) - new Date(b.date));

  const colors = weeklyData.map(d => d.colorCode);
  res.json(colors);
});

app.listen(port, () => {
  console.log(`Backend server listening at http://localhost:${port}`);
});