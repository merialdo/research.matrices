import React from 'react';
import './css/Input.css';
import {Editor} from './Editor';
import TextEditor from './TextEditor';
import update from 'immutability-helper';
import boundingbox_placeholder from './images/boundingbox_grey.png';
import { Button } from 'semantic-ui-react';
import './css/filter.css';
import axios from 'axios';
import {MultiOutput} from './AAright'
import RightCardSinglePage from './RightCardSinglePage';
import Loader from 'react-loader-spinner'
import LoadingOverlay from 'react-loading-overlay';
import { saveAs } from "file-saver";
import styled from 'styled-components';
var JSZip = require("jszip");



const Left = styled.div`
  display: inline-block;
  width : ${props =>{
    if (props.toggleLeft === true && props.toggleRight === true ) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false ) return "0%"
    if (props.toggleLeft === false && props.toggleRight === true) return "50%"
    else return "25%"
  }};
  max-width: ${props =>{
    if (props.toggleLeft === true && props.toggleRight === true ) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false ) return "0%"
    if (props.toggleLeft === false && props.toggleRight === true) return "50%"
    else return "25%"
  }};
  height : 100vh;
  max-height: 100vh;
  background : #f8f9fa;
  overflow: auto;
  border: ${props =>{
    if (props.toggleLeft === true && props.toggleRight === true ) return "0px "
    if (props.toggleLeft === true && props.toggleRight === false ) return "0px "
    else return "1px solid #f8f9fa"
  }};
`
const Right = styled.div`
  display: inline-block;
  width : ${props =>{
    if (props.toggleRight === true && props.toggleLeft === true ) return "0%"
    if (props.toggleRight === true && props.toggleLeft === false ) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false) return "25%"
    else return "25%"
  }};
  max-width: ${props =>{
    if (props.toggleRight === true && props.toggleLeft === true ) return "0%"
    if (props.toggleRight === true && props.toggleLeft === false ) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false) return "50%"
    else return "25%"
  }};
  height : 100vh;
  max-height: 100vh;
  background : #f8f9fa;
  overflow: auto;
  border: ${props =>{
    if (props.toggleRight === true && props.toggleLeft === true ) return "0px "
    if (props.toggleRight === true && props.toggleLeft === false ) return "0px "
    else return "1px solid #f8f9fa"
  }};
`
const Center = styled.div`
  display: inline-block;
  width : ${props =>{
    if (props.toggleLeft === true && props.toggleRight === true) return "100%"
    if (props.toggleLeft === true && props.toggleRight === false) return "75%"
    else return "50%"
  }};
  height : 100vh;
  max-height: 100vh;
  overflow: hidden;
  border: 1px solid #f8f9fa;
`
const Frame = styled.div`
  width : ${props =>{
    if (props.toggleLeft === true && props.toggleRight === true ) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false ) return "0%"
    if (props.toggleLeft === false && props.toggleRight === true) return "25%"
    else return "50%"
  }};
  height : 150px;
  border: 1px solid #f8f9fa;
  transition: all 0.3s ease;
  text-align: center;
  &:hover{
    background : #FFFFFF;
  }
`
const Img = styled.img`
  vertical-align: middle;
  transform: scale(0.8);
  max-height: 100%;
  max-width: 100%;
  transition: box-shadow 0.3s ease-in-out;
  ${Frame}:hover & {
    box-shadow: ${props => {
      if ( props.active_id === props.personal_index) {return " 5px -5px 0px #007bff";}
      else return " 5px -5px 0px  #A9A9A9;";
    }};
  }
  box-shadow: ${props => {
    if ( props.active_id === props.personal_index) {return " 5px -5px 0px #007bff";}
    else return " 5px -5px 0px rgba(0,0,0,0)";
  }};
`
const Icon = styled.i`
position: absolute;
bottom:5px;
transition: all 0.3s ease-in-out;
left:5px;
color: ${props => {
  if (props.is_confirmed) return "#7cfc00";
  if ( props.list_length>0) {return "#ffae1a";}
  else return "rgba(0,0,0,0)";
}};
`
const Toolbar = styled.div`
  flex: 0 1 auto;
  border-bottom: solid gray 0px;
  padding: 5px 10px;
  background: #f8f9fa;
`;

const TO_ANNOTATE = 'TO ANNOTATE!!!'

class MultiPageEditor extends React.Component {

  constructor(props) {
    super(props);
      this.state = {
        toggleLeft :false,
        toggleRight:false,
        index_active_file_in_files : null,
        files: this.props.location.state.fromRedirect.sort((a, b) => parseFloat(a.index) - parseFloat(b.index)),
        active_file :null,
        highlighted_box : -1,
        list_length : 0,
        filter: 0,
        disabled : false,
        dataset_name : this.props.location.state.dataset_name,
        dataset_id : this.props.location.state.dataset_id,
        is_from_creation : this.props.location.state.is_from_creation,
        loading : false,
      }
    }

     handleAddBox = (lista_id, new_boxes, max_id) => {
      if(JSON.stringify(this.state.files[this.state.index_active_file_in_files].boxes) !== JSON.stringify(new_boxes)){
        this.setState({list_length : new_boxes.length},() =>
      this.setState({
        files: update(this.state.files, {[this.state.index_active_file_in_files]: {boxes: {$set: new_boxes}, max_id: {$set: max_id}}}),
      }))
      } else {
      this.setState({list_length : new_boxes.length},() =>
      this.setState({
        files: update(this.state.files, {[this.state.index_active_file_in_files]: {boxes: {$set: new_boxes},max_id : {$set: max_id}}}),
      }))
    }
    }

    updateTextResponse = (new_text_response) => {
      this.setState({
        files: update(this.state.files, {[this.state.index_active_file_in_files]: {text_response : {$set: new_text_response}}}),
      })
    }

    set_confirmation = () =>{
      this.setState({
        files: update(this.state.files, {[this.state.index_active_file_in_files]: {is_confirmed : {$set: true}}}),
      })
    }

    togglefilter0 =()=> {
        this.setState({loading:true});
        let form_data = new FormData();
        this.state.files.forEach(f => form_data.append(f.filename, f.file))
        let url = 'http://localhost:5015/mybiros/api/v1/text-detection/corpus/';
        axios.post(url, form_data, {
            headers: {
            'content-type': 'multipart/form-data',
            }
            }).then(response => {
                let boxes_from_segmentation = response.data.segmentation
                boxes_from_segmentation.sort((el1,el2) => el1.y - el2.y)

                for(let i=0; i< this.state.files.length; i++){
                  this.setState({
                    files: update(this.state.files, {[i]: {boxes : {$set: boxes_from_segmentation[i][this.state.files[i].filename]['bounding_box']}}}),
                  })
                }
                this.setState({items: boxes_from_segmentation, loading: false});
              })
              .catch(err => {console.log(err); this.setState({loading:false})})

    }
    togglefilter1 =()=> {

      this.setState({loading:true});

      for(let i = 0; i<this.state.files.length; i++){

        let form_data = new FormData();
        form_data.append('file', this.state.files[i].file);
        form_data.append('boxes', JSON.stringify(this.state.files[i].boxes))
        let url_predict = 'http://localhost:5025/ocr'
        axios.post(url_predict, form_data, {
          headers: {
            'content-type': 'multipart/form-data',
          }
        })
            .then(response => {
              let lista = []
              for(let j=0; j<this.state.files[i].boxes.length; j++){
                let elem = {'id': this.state.files[i].boxes[j].id , 'text': response.data.predictions[j] ? response.data.predictions[j] : ''}
                lista.push(elem)
              }

              this.setState({
                files: update(this.state.files, {[i]: {text_response : {$set: lista}}})
              })
            })

            .catch(err => console.log(err), this.setState({loading:false}))

    }

    this.setState({loading:false})
  }


    async_set_segmentation_boxes =(index_file,boxes_from_segmentation) => {
      this.setState({
        files: update(this.state.files, {[index_file]: {boxes : {$set: boxes_from_segmentation}}}),
      })
    }

    deleteTextLine = (id) => {
      let new_boxes = this.state.files[this.state.index_active_file_in_files].boxes.filter(obj=>{return obj.id !== id})
      this.setState({
        files: update(this.state.files, {[this.state.index_active_file_in_files]: {boxes : {$set: new_boxes},is_confirmed:{$set : false}}}),
      },()=>{this.setState({active_file:this.state.files[this.state.index_active_file_in_files]})})
    }


    premilo = () => {
      let lisii = []
      this.state.files[this.state.index_active_file_in_files].boxes.forEach(box => lisii.push({"id":box.id,"text":"Ferdinando II"}) )
      this.setState({
        files: update(this.state.files, {[this.state.index_active_file_in_files]: {text_response : {$set: lisii}}}),
      })
    }

    download_collection = () => {
      var zip = new JSZip();
      let files = this.state.files
      for(let i=0;i<files.length;i++){
        let name = files[i].filename
        let stringa = ""
        let text_response = files[i].text_response
        for(let j=0;j<text_response.length;j++){
          stringa = stringa.concat(text_response[j].text)
          stringa = stringa.concat("\n")
        }
        zip.file(name.concat(".txt"), stringa);
      }
      zip.generateAsync({type:"blob"}).then(function(content) {
        // see FileSaver.js
        saveAs(content, "MyCollection.zip");
    })
    }

    createDataset = () => {
        let form_data = new FormData();
        form_data.append('name', 'corpus-lines-result')
        this.state.files.forEach(f => form_data.append(f.filename, f.file))

        let labels = this.createAnnotationsMongo(this.state.files)
        form_data.append('annotations', JSON.stringify(labels))

        let url = 'http://localhost:5000/api/dataset-creator';
        axios.post(url, form_data, {
            headers: {
                'content-type': 'multipart/form-data',
            }
        }).catch(err => console.log(err))
    }

    createAnnotationsMongo(files) {
        let labels = {}
        for (let i = 0; i < files.length; i++) {
            let name = files[i].filename
            let boxes = []
            for (let j = 0; j < files[i].boxes.length; j++) {
                let file = files[i]
                let box = {}

                box['id'] = file.boxes[j].id
                box['x'] = file.boxes[j].x
                box['y'] = file.boxes[j].y
                box['width'] = file.boxes[j].width
                box['height'] = file.boxes[j].height
                box['text'] = file.text_response[j].text
                boxes.push(box)
            }
            labels[name] = {
                "boxes": boxes,
                'list_active_texts': files[i].list_active_texts,
                'is_confirmed': files[i].is_confirmed,
                'index': files[i].index
            }
        }

        return labels

    }


    callDatasetCreator = () => {
        this.createDataset()
    }

    render() {
        const items = []

        let filtered = this.state.files
        if (this.state.files!== undefined) {
        for (const [index, value] of filtered.entries()) {
            items.push(
            <Frame toggleLeft={this.state.toggleLeft} toggleRight={this.state.toggleRight} key={index}  className="frame" onClick={v=>this.setState({index_active_file_in_files : value.index , active_file : filtered[index], list_length : value.boxes.length})}>
                <span className="helper"></span><Img active_id={this.state.index_active_file_in_files} personal_index = {filtered[index].index} src={value.file_url} alt="" /><Icon is_confirmed={value.is_confirmed} list_length={value.boxes.length} className="fa fa-check-circle"></Icon>
            </Frame>)
          }
        }

      return (
        <LoadingOverlay
            active={this.state.loading}
            spinner={<Loader
              type="Grid"
              color="#00BFFF"
              height={100}
              width={100}
           />}
          >
        <div style={{textAlign:"center"}}>
          {/*<button onClick={this.premilo} className="btn btn-primary"> send segmented image to predict service </button>
          <button onClick={this.download_collection} className="btn btn-primary">download all documents transcription</button>*/}
          <br/>

      {/* Body container  */}

          <div className="containerone ">

          <div className="icon-bar-try">
            <button  onClick={() => {this.setState({ toggleLeft: !this.state.toggleLeft })}} className ="buttonVertical-try btn-primary">
              <i className="fa fa-picture-o fa-1x ico"></i> Images
            </button>
          </div>
          <div className="icon-bar-right-try">
            <button onClick={() => { this.setState({ toggleRight: !this.state.toggleRight })}} className ="buttonVertical-try btn-primary">
              <i className="fa fa-tag fa-1x ico"></i> Annotations
            </button>
          </div>

            <div>
              <Left style={{ pointerEvents: this.state.disabled ? 'none' : 'auto' }} toggleLeft={this.state.toggleLeft} toggleRight={this.state.toggleRight}>
                <div className="container">

                <div>
                  <Button.Group basic widths="2">
                    <Button id ="botn" compact onClick={this.togglefilter0}>Segment ALL images</Button>
                    <Button id ="botn" compact onClick={this.togglefilter1}>Transcribe ALL images</Button>
                      <Button id ="botn" compact onClick={this.callDatasetCreator}>Download Lines Result</Button>
                  </Button.Group>
                </div>

                  <div className="row">
                    {items.length ? items : null}
                  </div>
                </div>
              </Left>
              <Center toggleLeft={this.state.toggleLeft} toggleRight={this.state.toggleRight}>
                <Editor active_file = {this.state.active_file} setSegmentationBoxes = {this.setSegmentationBoxes}
                onAddBox={this.handleAddBox} highlighted_box = {this.state.highlighted_box}
                set_highlight_box_on_rect_click = {id => this.setState({highlighted_box : id})}
                set_text_response_from_segmentation={this.updateTextResponse}
                async_set_segmentation_boxes = {this.async_set_segmentation_boxes}
                disableGallery={()=>this.setState({disabled:true})} enableGallery={()=>this.setState({disabled:false})}
                />
              </Center>

              <Right toggleLeft={this.state.toggleLeft} toggleRight={this.state.toggleRight}>

              {this.state.index_active_file_in_files!== null ? (
                <>
                <Toolbar>
                  <Button basic id ="botn" compact onClick={this.download_collection}>Download all .txt</Button>
                </Toolbar>
                <div className="right_single_page"><RightCardSinglePage
                text_lines = {this.state.files[this.state.index_active_file_in_files].text_response}
                highlight_rect_on_start_text_edit = {id => this.setState({highlighted_box : id})}
                updateTextResponse={this.updateTextResponse} highlighted_box={this.state.highlighted_box}
                /></div>
                </>
                ):(
                  <div>
                  <div className="bbplaceholder">
                    <img className="img_placeholder_annotation" alt="" src={boundingbox_placeholder}></img>
                  </div>
                  <div className="text-center text_placeholder">
                    <p>Your output will appear here!</p>
                  </div>
                  </div>
                  )}
              </Right>

            </div>
          </div>
        </div>
         {/* Footer */}
    <div>
        <footer className="py-5 bg-dark">
            <div className="container">
                <p className="m-0 text-center text-white">HTR service DEMO</p>
            </div>
        </footer>


        <script src="vendor/jquery/jquery.min.js"></script>
        <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    </div>
    {/* End of Footer */}
        </LoadingOverlay>


          );
        }
      }

export { MultiPageEditor };
