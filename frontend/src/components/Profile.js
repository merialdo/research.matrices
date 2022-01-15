import React from 'react';

import { Tab, Segment, Modal, Button } from 'semantic-ui-react'
import { Link } from 'react-router-dom'
import axios from 'axios';
import update from 'immutability-helper';
import './css/modal.css'

export default class Profile extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      list_dataset: this.props.dataset,
      list_models: this.props.models,
      is_loading: true,
    }
  }

  deleteDataset = (event,index) => {
    const resource = "http://localhost:5000/api/datasets/"+this.state.list_dataset[index].id
    axios.delete(resource, {headers: {}}
    ).then((response)=>{
        this.setState({
        list_dataset: update(this.state.list_dataset,{ $splice: [[index, 1]] } )
      })
    })
  }


  getDatasetFields = (JSON, index) => {
    var self = this;
    let list_dataset_images = [];
    for (let i = 0; i < JSON.data.data.length; i++) {
      let curr_image = JSON.data.data[i];
      let index_curr_image = curr_image.index
      let boxes = [];
      let text_response = [];
      let filename = curr_image.filename
      for (let u = 0; u < curr_image.annotations.length; u++) {
        let new_box = { "id": u + 1, "x": curr_image.annotations[u].x, "y": curr_image.annotations[u].y, "width": curr_image.annotations[u].width, "height": curr_image.annotations[u].height }
        let new_text = { "id": u + 1, "text": curr_image.annotations[u].text }
        boxes.push(new_box);
        text_response.push(new_text);
      }
      let url_img = 'http://localhost:5000/api/datasets/getimage/' + JSON.data._id['$oid'] + '/' + curr_image.image['$oid']
      axios.get(url_img, {
        responseType: 'blob',
        headers: {}
      }).then(response => {
        let new_ele = {}
        new_ele = {
          "filename": filename,
          "file": response.data,
          "file_url": window.URL.createObjectURL(response.data),
          "boxes": boxes,
          "max_id": boxes.length + 1,
          "text_response": text_response,
          "list_active_texts": [],
          "is_confirmed": false,
          "index": index_curr_image
        }
        list_dataset_images.push(new_ele);
        if (i === JSON.data.data.length - 1) { self.setState({ is_loading: false }) }
      })
    }

    this.setState({
      list_dataset: update(this.state.list_dataset, { [index]: { img: { $set: list_dataset_images } } }),
    })
  }

  render() {
    let your_models = []
    if (this.state.list_models.length !== 0) {
      for (const [index, value] of this.state.list_models.entries()) {
        your_models.push(
          <Segment key={index} raised style={{'borderRadius': '0px'}}>
            <Modal size={"small"} key={index} trigger={<button className="btn btn-link" >{value.name}</button>}>
              <Modal.Header>{value.name}</Modal.Header>
              <Modal.Content image>
                <div>
                  <br />
                  <i>Model Name : </i> <b>{value.name}</b>
                  <br />
                  <i>Language : </i> <b>{value.lang}</b>
                  <br />
                  <i>Description : </i> <b>{value.desc}</b>
                </div>

              </Modal.Content>
            </Modal>
          </Segment>
        )
      }
    }

    let your_dataset = []
    if (this.state.list_dataset.length !== 0) {
      for (const [index, value] of this.state.list_dataset.entries()) {
        your_dataset.push(
            <>

          <Segment key={index} raised style={{'borderRadius': '0px'}}>
            <Modal size={"small"} onClose={() => this.setState({ is_loading: true })} key={index} trigger={<button className="btn btn-link" onClick={() => this.getDatasetFields(value.json, index)}>{value.name}</button>}>
              <Modal.Header style={{'borderRadius': '0px'}}>{value.name}</Modal.Header>
              <Modal.Content image>
                <p>Descrizione</p>
              </Modal.Content>
              <Modal.Actions>
                {this.state.is_loading ? (<Button loading primary>
                  Loading
                </Button>) : (
                    <>


                      <Button className={"btn btn-danger"} key={index} onClick={(e) => {if (window.confirm('Are you sure you wish to delete this item?')) {this.deleteDataset(e, index)}}}>delete</Button>
                    <Link
                      to={{
                        pathname: "/annotationEditor",
                        state: { fromRedirect: this.state.list_dataset[index].img, dataset_id: value.id, dataset_name: value.name, is_from_creation: false }
                      }}
                    ><button key={index} className="btn btn-primary" >Go to annotation editor</button>

                    </Link>

                  </>)
                }
              </Modal.Actions>
            </Modal>

          </Segment>

            </>



        )
      }
    }
    const panes = [
      {
        menuItem: 'Datasets',
        render: () => <Tab.Pane attached={false} ><div className="card-text">{your_dataset.length !== 0 ? your_dataset : "NO dataset yet"}</div></Tab.Pane>,
      },
      {
        menuItem: 'Models',
        render: () => <Tab.Pane attached={false}>{your_models.length !== 0 ? your_models : "NO Models yet"}</Tab.Pane>,
      },
    ]
    return (
      <div>
        <Tab menu={{ tabular: false }} panes={panes} style={{'marginBottom':'10vh', 'borderRadius': '0px'}}/>
      </div>
    );
  }
}
