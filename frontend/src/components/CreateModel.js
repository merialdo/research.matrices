import React from 'react'
import { Step, Segment, Modal, Form, Button } from 'semantic-ui-react'
import axios from 'axios';
import update from 'immutability-helper';
import Walle from './images/Walle.gif'
/* import D3ExampleGraph from './D3ExampleGraph'
 */
class CreateModel extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      list_dataset: [],
      choosed_dataset: null,
      open_modal_dataset: false,
      open_modal_info: false,
      model: {},
      model_fi: null,
      is_started: false,
    };
  }

  componentDidMount() {
  }

  componentDidUpdate(prevProps, prevState) {
    console.log(this.state)
  }

  handleClick = (e, { id }) => {
    this.setState({ active: id })
    if (id === "Dataset") { this.setState({ open_modal_dataset: true }) }
    if (id === "Model") { this.setState({ open_modal_info: true }) }
  }

  handleChange = (e, { name, value }) => this.setState({
    model: update(this.state.model, { [name]: { $set: value } }),
  })
  handleSubmit = () => {
    const { model } = this.state
    this.setState({ model_fi: model, open_modal_info: false }, () => { console.log(this.state.model_fi) })
  }

  sendTrainingInfo = () => {
    this.setState({ is_started: true })
    let formData = new FormData()
    let url_train = 'http://localhost:5000/api/htr/training'

    formData.append('model_name', this.state.model_fi.Name)
    formData.append('epochs', this.state.model_fi.Epochs)
    formData.append('training_data', this.state.choosed_dataset.name)

    try {
      axios.post(url_train, formData, {
        headers: {
          'content-type': 'application/json',
        }

      })

    }
    catch (error) {
      console.log(error)
    }
  }

  render() {
    let model_info = null;
    if (this.state.model_fi !== null) {
      model_info = <div>
        <br />
        <i>Model Name : </i> <b>{this.state.model_fi.Name}</b>
        <br />
        <i>Number of Epochs : </i> <b>{this.state.model_fi.Epochs}</b>
      </div>
    }

    const { active, model } = this.state
    let your_dataset = []
    if (this.state.list_dataset.length !== 0) {
      for (const [index, value] of this.state.list_dataset.entries()) {
        your_dataset.push(
          <Segment key={index} raised>
            <button className="btn btn-link" onClick={() => this.setState({ choosed_dataset: { "name": value.name, "id": value.id } }, () => { this.setState({ open_modal_dataset: false }) })}>{value.name}</button>
          </Segment>
        )
      }
    }

    return (
      <div>
        {/* Header */}
        <header className="bg-light py-5 ">
          <div className="container h-100">
            <div className="row h-100 align-items-center">
              <div className=".col-6 .col-md-4">
                <h1 className="display-4 text-dark mt-5 mb-2">Create Your Model
            <button type="button" className="btn btn-link mt-3">Info</button>
                </h1>
                <p className="text-secondary pt-4">Select a Dataset among the ones in your collection, insert basic ML parameters and start the training</p>
              </div>
              <div>
              </div>
            </div>
          </div>
        </header>
        <br />
        <br />
        {this.state.is_started ? 
        <div style={{ textAlign: "center", height: "100vh" }}>


          <h1 className="display-4 text-dark mt-5 mb-2">Well Done! Your training has started!
          </h1>
          <p className="text-secondary pt-4">You will recieve an alert when your model is ready to be used! in the meantime enjoy this gif :)</p>
          <img src={Walle} alt="walle"></img>
          
          
          </div>
        


          
          
          :
          <Step.Group unstackable ordered widths={3}>
            <Step completed={this.state.choosed_dataset !== null} active={active === 'Dataset'}
              link
              onClick={this.handleClick}
              id='Dataset'
            >
              <Step.Content>
                <Step.Title>Choose Training Data</Step.Title>
                <Step.Description>Please Choose a Dataset among the ones in your collection</Step.Description>
                <br />
                {this.state.choosed_dataset === null ? <i>No Dataset choosed yet</i> : <div><i>Dataset choosed : </i> <b>{this.state.choosed_dataset.name}</b></div>}
                <br />
                <br />
                <Modal open={this.state.open_modal_dataset === true} onClose={() => this.setState({ open_modal_dataset: false })} size={"small"} >
                  <Modal.Header>Your Dataset List</Modal.Header>
                  <Modal.Content >
                    {your_dataset}
                  </Modal.Content>
                </Modal>

              </Step.Content>
            </Step>
            <Step completed={this.state.model_fi !== null}
              active={active === 'Model'}
              link
              onClick={this.handleClick}
              id='Model'>
              <Step.Content>
                <Step.Title>Model</Step.Title>
                <Step.Description>Please insert ML parameters and the model basic informations</Step.Description>
                {this.state.model_fi !== null ? model_info : null}
                <Modal open={this.state.open_modal_info} onClose={() => this.setState({ open_modal_info: false })} size={"small"} >
                  <Modal.Header>Your Model Informations</Modal.Header>
                  <Modal.Content >

                    <Form onSubmit={this.handleSubmit}>
                      <Form.Group>
                        <Form.Input
                          label='Model Name'
                          placeholder='Model Name'
                          name='Name'
                          value={model.name}
                          onChange={this.handleChange}
                          autocomplete="off"
                        />
                        <Form.Input
                          label='Number of Epochs'
                          placeholder='Number of Epochs'
                          name='Epochs'
                          value={model.epochs}
                          onChange={this.handleChange}
                          type="number"
                        />
                        <Form.Button content='Submit' />
                      </Form.Group>
                    </Form>

                  </Modal.Content>
                </Modal>
              </Step.Content>
            </Step>
            <Step active={active === 'Results'}
              link
              onClick={this.handleClick}
              id='Results'>
              <Step.Content>
                <Step.Title>Start training</Step.Title>
                <Step.Description>Start the training service</Step.Description>
                <Button disabled={this.state.choosed_dataset === null || this.state.model_fi === null} onClick={this.sendTrainingInfo}> Press to send</Button>
              </Step.Content>
            </Step>
          </Step.Group>}

        {/* Footer */}
        <div className="mt-3">
          <footer className="py-5 bg-dark">
            <div className="container">
              <p className="m-0 text-center text-white">HTR service DEMO</p>
            </div>
          </footer>


          <script src="vendor/jquery/jquery.min.js"></script>
          <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
        </div>
        {/* End of Footer */}
      </div>
    )
  }
}

export { CreateModel }