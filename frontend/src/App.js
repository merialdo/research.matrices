import React, { Component } from 'react';
import { Navigation} from './components/Navigation';
import { Main } from './components/Main';
import './App.css';

class App extends Component {


  render() {
    return (
      <div >
        <Navigation />
        <Main />
      </div>
    );
  }
}

export default App;
