import './App.css';
import Notepad from './Notepad';
import {Routes, Route} from 'react-router-dom';

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path = "/" element = {<Notepad />} />
      </Routes>
      
    </div>
  );
}

export default App;
