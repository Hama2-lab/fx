import "./App.css";
import "./reset.css";
import { useEffect, useState } from "react";
import React from "react";
import {
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  LineChart,
  Line,
} from "recharts";

const symbols = ["JPY", "USD", "EUR"];

const useFetchData = (from, to) => {
  const [closeData, setCloseData] = useState();
  const [predictionsData, setPredictionsData] = useState();
  useEffect(() => {
    (async () => {
      const result = await fetch(
        `http://localhost:8000/fx?from_=${from}&to_=${to}`
      );
      const json = await result.json();
      if (json.train && json.valid) {
        const close = [
          ...Object.entries(JSON.parse(json.train).close),
          ...Object.entries(JSON.parse(json.valid).close),
        ].map((item) => ({ name: item[0], close: item[1] }));

        const prediction = [
          ...Object.entries(JSON.parse(json.valid)["Predictions"]),
        ].map((item) => ({ name: item[0], predictions: item[1] }));

        setCloseData(close);
        setPredictionsData(prediction);
      }
    })();
  }, [from, to]);

  return { closeData, predictionsData };
};

function App() {
  const [from, setFrom] = useState("USD");
  const [to, setTo] = useState("JPY");

  const { closeData, predictionsData } = useFetchData(from, to);

  const dataSet = (closeData || []).map((item) => {
    const matched = predictionsData?.find((i) => i.name === item.name);
    if (matched) return { ...item, ...matched };
    else return item;
  });

  console.log(dataSet);
  return (
    <div>
      {/* {JSON.stringify(data)} */}
      <span>from</span>
      <select
        name="from"
        value={from}
        onChange={(e) => setFrom(e.target.value)}
      >
        {symbols.map((item) => (
          <option value={item}>{item}</option>
        ))}
      </select>

      <span>to</span>
      <select name="to" value={to} onChange={(e) => setTo(e.target.value)}>
        {symbols.map((item) => (
          <option value={item}>{item}</option>
        ))}
      </select>

      <LineChart
        width={500}
        height={300}
        data={dataSet}
        options={{
          elements: {
            point: {
              radius: 0,
            },
          },
        }}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="close"
          stroke="#0000ff"
          dot={false}
          // activeDot={{ r: 8 }}
        />
        <Line
          type="monotone"
          dataKey="predictions"
          stroke="#f20202"
          dot={false}
          // activeDot={{ r: 8 }}
        />
      </LineChart>
    </div>
  );
}
export default App;
