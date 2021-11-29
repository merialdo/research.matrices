import React from 'react';
import { NavLink } from 'react-router-dom';

class Navigation extends React.Component {
  state={
    is_logged_in : false,
  }
  componentDidMount(){
    if (localStorage.getItem("access_token") !== null && localStorage.getItem("access_token")!==undefined) {
      this.setState({is_logged_in:true})
    }
    else{ this.setState ({is_logged_in:false})}
  }

  resetValues= () =>{
    this.setState({is_logged_in:false})
    localStorage.removeItem("access_token")
  }

  render() {
    const navItemLogged = <ul className="navbar-nav ml-auto">
<li className="nav-item">
<NavLink
  exact
  onClick={()=>console.log(localStorage.getItem("access_token"))}
  to="/UserDashboard"
  className="nav-link"
  activeStyle={{ fontWeight: 'bold' }}
>
  Home
</NavLink>
</li>
<li className="nav-item">
<NavLink
  exact
  onClick={this.resetValues}
  to="/"
  className="nav-link"
  activeStyle={{ fontWeight: 'bold' }}
>
  Logout
</NavLink>
</li>
</ul>

const navItemNotLogged = <ul className="navbar-nav ml-auto">
<li className="nav-item">
<NavLink
  exact
  to="/"
  className="nav-link"
  activeStyle={{ fontWeight: 'bold' }}
>
  Home
</NavLink>
</li>
<li className="nav-item">
<NavLink
  exact
  to="/login"
  className="nav-link"
  activeStyle={{ fontWeight: 'bold' }}
>
  Login
</NavLink>
</li>
</ul>

    return (
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary ">
      <div className="container">
        <div>
        <a className="navbar-brand ml-auto" href="/UserDashboard">HTR service</a>
        </div>
        <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarResponsive" aria-controls="navbarResponsive" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarResponsive">
          {this.state.is_logged_in ?  navItemLogged:navItemNotLogged}
        </div>
      </div>
    </nav>

    );
}
}

export { Navigation };
