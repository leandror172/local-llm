import React, { useState } from 'react';
import './App.css';

interface Item {
  id: number;
  name: string;
}

export const App: React.FC = () => {
  const [items, setItems] = useState<Item[]>([]);
  const [input, setInput] = useState('');

  const addItem = () => {
    if (input.trim()) {
      setItems([...items, { id: Date.now(), name: input }]);
      setInput('');
    }
  };

  return (
    <div className="App">
      <h1>React Todo App</h1>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Add an item..."
      />
      <button onClick={addItem}>Add</button>
      <ul>
        {items.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
};
