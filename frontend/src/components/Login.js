import React, {Component} from "react";
import {Button, ControlLabel, FormControl, FormGroup, HelpBlock} from "react-bootstrap";
import './css/login.css';

function FieldGroup({id, label, help, ...props}) {
    return (
        <FormGroup controlId={id}>
            <ControlLabel>{label}</ControlLabel>
            <FormControl {...props} />
            {help && <HelpBlock>{help}</HelpBlock>}
        </FormGroup>
    );
}

export default class Login extends Component {
    constructor(props) {
        super(props);

        this.state = {
            username: "",
            password: "",
            email: "",
            new_user: false,
        }


    }

    componentDidUpdate(prevState) {
        if (prevState !== this.state) {
            console.log(this.state.new_user)
        }
    }

    handleChange = event => {
        const target = event.target;
        const value = target.value;
        const name = target.name;
        this.setState({
            [name]: value
        });
    }

    goToRegister = () => {
        this.setState({new_user: !this.state.new_user})
    }

    handleRegistration = e => {
        e.preventDefault();
        let url = "http://localhost:5000/api/auth/signup"

        const data = {
            username: this.state.username, password: this.state.password,
            email: this.state.email
        }

        fetch(url, {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {'Content-Type': 'application/json'}
        }).then(res => res.json())
            .then(data => {
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('username', data.username);

            }).catch(err => console.log(err));

        this.setState({
            new_user: false
        })
    }

    handleSignIn = e => {
        e.preventDefault();
        let url = "http://localhost:5000/api/auth/login"
        const data = {email: this.state.email, password: this.state.password}

        fetch(url, {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {'Content-Type': 'application/json'}
        }).then(res => res.json())
            .then(data => {
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user_id', data.id);
                console.log(data.access_token)
                localStorage.setItem('user_email', this.state.email);
                console.log(data.username)

                if (localStorage.getItem("access_token") !== null && localStorage.getItem("access_token") !== undefined) {
                    window.location.replace("/UserDashboard")
                } else {
                    alert(data.error);
                }
            }).catch(err => console.log(err));
    }


    render() {

        if (this.state.new_user === true) {

            return (
                <section className="auth-section signup-section text-center py-5"
                         style={{backgroundColor: "rgba(0,0,0,0.02)"}}>
                    <div className="container">
                        <div className="auth-wrapper mx-auto shadow p-5 rounded">


                            <div>
                                <h2 className="auth-heading text-center mb-3">Start Your Free trial today</h2>
                                {/*
                     <div className="social-auth text-center mx-auto">
					        <ul className="social-buttons list-unstyled">
						        <li className="mb-3">
							        <button className="btn-social btn-block btn-link">
								        <span className="icon-holder"><img src={googlelogo} className="social-logo"alt=""/></span>
								        <span className="btn-text">Sign up with Google</span>
							        </button>
						        </li>
						        <li className="mb-3"><button className="btn-social btn-block btn-link"><span className="icon-holder"><span className="icon-holder"><img src={microsoftlogo} className="social-logo" alt=""/></span></span><span className="btn-text">Sign up with Microsoft</span></button></li>
					        </ul>
				        </div>



                                <div className="divider my-5">
                                    <span className="or-text">OR</span>
                                </div>
                                 */}

                                <div className="LoginForm">
                                    <form>

                                        <FieldGroup
                                            id="formControlsUsername"
                                            type="username"
                                            name="username"
                                            value={this.state.username}
                                            onChange={this.handleChange}
                                            placeholder="Username"
                                        />

                                        <FieldGroup
                                            id="formControlsEmail"
                                            type="email"
                                            name="email"
                                            value={this.state.email}
                                            onChange={this.handleChange}
                                            placeholder="Your Email"
                                        />

                                        <FieldGroup
                                            id="formControlsPassword"
                                            type="password"
                                            name="password"
                                            value={this.state.password}
                                            onChange={this.handleChange}
                                            placeholder="Password"/>


                                        <Button onClick={this.handleRegistration}
                                                className="btn btn-primary btn-lg center btn-register"> Register</Button>
                                    </form>
                                    <div className="auth-option text-center pt-5 already_account">
                                        Already have an account? <button type="button" className="btn btn-link"
                                                                         onClick={this.goToRegister}>Log in</button>
                                    </div>

                                </div>

                            </div>
                        </div>
                    </div>
                </section>
            );
        } else {
            return (
                <section className="auth-section signup-section text-center py-5"
                         style={{backgroundColor: "rgba(0,0,0,0.02)"}}>
                    <div className="container">
                        <div className="auth-wrapper mx-auto shadow p-5 rounded">


                            <div>
                                <h2 className="auth-heading text-center mb-3">Go to Your Riserverd Area</h2>

                                <div className="LoginForm">
                                    <form>


                                        <FieldGroup
                                            id="formControlsEmail"
                                            type="email"
                                            name="email"
                                            value={this.state.email}
                                            onChange={this.handleChange}
                                            placeholder="Your Email"
                                        />

                                        <FieldGroup
                                            id="formControlsPassword"
                                            type="password"
                                            name="password"
                                            value={this.state.password}
                                            onChange={this.handleChange}
                                            placeholder="Password"/>


                                        <Button onClick={this.handleSignIn}
                                                className="btn btn-primary btn-lg center btn-register"
                                                style={{marginBottom: "15px"}}> Log-In with Us</Button>
                                    </form>
                                    {/* <div className="social-auth text-center mx-auto">
            <ul className="social-buttons list-unstyled">
              <li className="mb-3">
                <button className="btn-social btn-block btn-link">
                  <span className="icon-holder"><img src={googlelogo} className="social-logo" alt=""/></span>
                  <span className="btn-text">Log in with Google</span>
                </button>
              </li>
              <li className="mb-3"><button className="btn-social btn-block btn-link"><span className="icon-holder"><span className="icon-holder"><img src={microsoftlogo} className="social-logo" alt=""/></span></span><span className="btn-text">Log in with Microsoft</span></button></li>
            </ul>
          </div>*/}


                                </div>
                                <div className="auth-option text-center pt-5 already_account">
                                    Don't have an account yet? <button type="button" className="btn btn-link"
                                                                       onClick={this.goToRegister}>Create a new
                                    one</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            )
        }
    }
}
