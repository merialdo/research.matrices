import React, { Component } from "react";
import './css/dashboard.css'; //css to better display input forms
import history from './images/history.png'
import train from './images/block.png'
import databack from './images/databack.png'
import axios from 'axios';
import Profile from './Profile';
import {Link} from 'react-router-dom'

export default class Dashboard extends Component{
  constructor(props){
    super(props);

    this.state = {
      list_dataset : [],
      list_models : [],
      is_loading : true,
      data_name : null,
    }
 }

 componentDidMount(){
 }

  render(){
    return(
      <>
        <div className="container-fluid" >
               <header className="dash-header py-5 text-center">
                  <h1 className="display-4">Welcome to HTR</h1>
              </header>
{/** START OF 3 CARDS */}
             <div  className="row justify-content-md-center row-services" >
              
             <div className="col-sm-3 pt-3 mb-5 mb-lg-0">
              <div className="card_profile card card-hover">
                      <div className="card-horizontal">
                          <div className="img-square-wrapper">
                              <img className="card-img-top" src={history} alt=""></img>
                          </div>
                          <div className="card-body">
                            <h3 className="card-title">Multipage</h3>
                            <hr></hr>
                            <p className="card-text inverse-reveal">Upload multiple documents and start the hand-written text recognition using your machine learning model of choice</p>
                            <div className="reveal p-2">
                              <Link
                              to={{
                                pathname: "/multiPageStaging",
                              }}
                              ><button className="btn btn-primary" >try multipage HTR</button>
                              </Link>                   
                            </div>
                          </div>
                      </div>
                </div>             
              </div>


              <div className="col-sm-3 pt-3 mb-5 mb-lg-0">

              <div className="card_profile card card-hover">
                      <div className="card-horizontal">
                          <div className="img-square-wrapper">
                              <img className="card-img-top" src={history} alt=""></img>
                          </div>
                          <div className="card-body">
                            <h3 className="card-title">Try HTR Service</h3>
                            <hr></hr>
                            <p className="card-text inverse-reveal">Upload a single document and start the hand-written text recognition using your machine learning model of choice</p>
                            <div className="reveal p-2">
                              <Link
                              to={{
                                pathname: "/singlePage",
                              }}
                              ><button className="btn btn-primary" >try HTR</button>
                              </Link>                   
                            </div>
                          </div>
                      </div>
                </div>             
              
              </div>
             
    
             <div className="col-sm-3 pt-3 mb-5 mb-lg-0">
              
             <div className="card_profile card card-hover">
                      <div className="card-horizontal">
                          <div className="img-square-wrapper">
                              <img className="card-img-top" src={databack} alt=""></img>
                          </div>
                          <div className="card-body">
                            <h4 className="card-title">Create Your Dataset</h4>
                            <hr></hr>
                            <p className="card-text inverse-reveal">Upload, annotate and store your dataset in our server</p>
                            <div className="reveal p-2">
                            <a href="/CreateDataset" className="btn btn-primary">Create Dataset</a>                    </div>
                          </div>
                      </div>
                </div>

              </div>

              <div className="col-sm-3 pt-3 mb-5 mb-lg-0">

                <div className="card_profile card card-hover">
                      <div className="card-horizontal">
                          <div className="img-square-wrapper">
                              <img className="card-img-top" src={train} alt=""></img>
                          </div>
                          <div className="card-body">
                            <h3 className="card-title">Create Your Model</h3>
                            <hr></hr>
                            <p className="card-text inverse-reveal">Choose the training data, select the parameters and start the training</p>
                            <div className="reveal p-2">
                            <a href="/CreateModel" className="btn btn-primary">Start Training</a>                    </div>
                          </div>
                      </div>
                </div>
                </div>

             </div>
{/** END OF 3 CARDS */}

             <div className="divider  my-5">
				          <span className="or-text profile-area"> <h6>Manage model and dataset</h6></span>
				    </div>
            
          <div className="container-fluid w-75">
          <div className="card" style={{'borderRadius': '0px'}}>
        </div>
            <Profile dataset={this.state.list_dataset} models ={this.state.list_models}/>
          </div>

             <div>
       

  
        <script src="vendor/jquery/jquery.min.js"></script>
        <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
        
    </div>

        
        </div>

      </>
    )
        
    }
}

