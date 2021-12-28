import React from 'react';
import './css/home.css';
import image_logo from './images/home_x4.png';
import hwrite from './images/hw_to_font.png'
import hwrite_ann from './images/hwrite_annotated.png'
import htr_eng from './images/htr_engine.png'

const Home = () => {

    return (
    <div>
    {/* Header */}
    <header className="brain">
        <div className="container">
            <div className="row h-100 align-items-center">
                <div className="col-12 col-lg-6 pt-3 mb-5 mb-lg-0">
                    <h1 className="site-headline font-weight-bold mb-3">HTR. Exploit your data</h1>
                        <hr></hr>
                        <div className="site-tagline mb-4">
                        The field of automated handwriting recognition has achieved significant real world success in targeted applications.
                        Turn your hand-writtend documents into precious value <b>now</b>!
                        </div>

                        <a href="/dashboard"><button className="btn btn-primary btn-lg" style={{marginRight:'10px'}}> Start </button></a>

                </div>
                <div className="col-12 col-lg-6 pt-3 mb-5 mb-lg-0">
                    <img className="logo" src={image_logo} alt=""></img>
                </div>
            </div>
        </div>
    </header>

    <section className="benefits-section theme-bg-light py-5">
        <div className="container">
        <h3 className="mb-2 text-center font-weight-bold section-title">Made For Handwriting</h3>
        <div className="mb-5 text-center section-intro">AI for human text recognition</div>
            <hr></hr>
            <div className="row">
                <section className="how-section py-5">
                    <div className="container">
                        <h3 className="mb-2 text-center font-weight-bold section-title">How Does It Work</h3>
                        <div className="mb-5 text-center section-intro">You're only a few simple steps away</div>
                        
                        <div className="row">
                            <div className="item col-12 col-md-4">
                                <div className="icon-holder">
                                    <img src={hwrite} alt=""></img>
                                </div>
                                <div className="desc p-3">
                                    <h5 className="text-center"><span className="step-count mr-2">1</span>Try Existing Model</h5>
                                    <p className="text-center">Before diving into the training section, try our service using pre-existing models</p>
                                </div>
                            </div>
                            <div className="item col-12 col-md-4">
                                <div className="icon-holder">
                                    <img src={hwrite_ann} alt=""></img>
                                    <div className="arrow-holder d-none d-lg-inline-block"></div>
                                </div>
                                <div className="desc p-3">
                                    <h5 className="text-center"><span className="step-count mr-2">2</span>Create Text Annotations</h5>
                                    <p className="text-center">Use our annotation editor to label your data in order to create training data for the AI engine</p>
                                </div>
                            </div>
                            <div className="item col-12 col-md-4">
                                <div className="icon-holder">
                                    <img src={htr_eng} alt=""></img>
                                </div>
                                <div className="desc p-3">
                                    <h5 className="text-center"><span className="step-count mr-2">3</span>Train Your Model</h5>
                                    <p className="text-center">Select the data and the desired setting and then launch the training</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    </section>

    
    {/* Footer */}
    <div>

  
        <script src="vendor/jquery/jquery.min.js"></script>
        <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    </div>
    {/* End of Footer */}
    
</div>

    );

}

export { Home };
