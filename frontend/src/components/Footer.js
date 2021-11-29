import React from 'react';
import { NavLink } from 'react-router-dom';

class Footer extends React.Component {


    render() {
        return (

            <footer className="py-5 bg-dark" style={{
                position:"fixed",
                left: 0,
                bottom: 0,
                width: '100%'}}
                    >
                <div className="container">
                    <p className="m-0 text-center text-white">HTR service DEMO</p>
                </div>
            </footer>


        )

    }

}



export { Footer };


