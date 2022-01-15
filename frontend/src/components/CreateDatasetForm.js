import React from 'react'
import './css/thumb.css'; //css to better display input forms
import {Container, Row, Col} from 'reactstrap'


class CreateDatasetForm extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            model_name: null,
            language: "LAT",
            description: null,
            choosed: false,

            options: [
                {
                    text: "Latin",
                    value: "1"
                },
                {
                    text: "English",
                    value: "2"
                },
                {
                    text: "Deutsch",
                    value: "3"
                },
                {
                    text: "Italian",
                    value: "4"
                },
            ]
        };

    }

    mySubmitHandler = (event) => {
        event.preventDefault();
        this.setState({
            model_name: event.target.model_name.value,
            language: event.target.language.value,
            description: event.target.description.value,
        })
        //callback here
        this.sendDataToParent()
    }


    myChangeHandler = (event) => {
        let nam = event.target.name;
        let val = event.target.value;
        this.setState({[nam]: val});
    };

    sendDataToParent = () => {
        // callback to send data to CreateYourModel component
        this.props.modelDataFormCallback({
            'name': this.state.model_name,
            'language': this.state.language || null,
            'description': this.state.description,
        });
    }


    render() {


        return (
            <div>

                <header className="bg-light py-5 mb-5">
                    <Container fluid="md">
                        <Row>
                            <Col sm="4">
                                <h1 className="display-4 text-dark mt-5 mb-2">Create Your Dataset
                                </h1>
                                <p className="text-secondary pt-4">Insert the basic information of your dataset and
                                    proceed to the next step</p>
                            </Col>


                            <Col sm="2"></Col>
                            <Col sm="4">
                                <form onSubmit={this.mySubmitHandler}>
                                    <p>Enter your Dataset name:</p>
                                    <input
                                        type="text"
                                        className="form-control"
                                        name='model_name'
                                        onChange={this.myChangeHandler}
                                        required
                                    />

                                    <hr></hr>
                                    <p>Enter dataset's language:</p>

                                    <select
                                        type="text"
                                        className="form-control"
                                        name='language'
                                        onChange={this.myChangeHandler}
                                        required
                                    >
                                        <option defaultValue value="LAT"> LAT</option>
                                        <option value="ITA"> ITA</option>
                                        <option value="ENG"> ENG</option>
                                        <option value="DEU"> DEU</option>
                                    </select>


                                    <hr></hr>
                                    <p>Enter dataset's description:</p>
                                    <textarea
                                        className="form-control"
                                        id="textArea"
                                        rows="5"
                                        name='description'
                                        onChange={this.myChangeHandler}
                                    ></textarea>
                                    <hr></hr>
                                    <p></p>
                                    <input className="btn btn-primary" type="submit" value="Go To Data Staging Area"/>

                                </form>
                            </Col>


                            <div className="col">


                            </div>
                        </Row>


                    </Container>
                </header>


            </div>
        )

    }
}

export {CreateDatasetForm}