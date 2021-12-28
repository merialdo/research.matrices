import React from 'react';
import './css/Input.css'; //css to better display input forms
import {LeftCardSinglePage} from './LeftCardSinglePage'
import * as jsPDF from 'jspdf';
import styled from 'styled-components';
import { PDFObject } from 'react-pdfobject';
import { Menu,Button, Tab,TextArea } from 'semantic-ui-react';
import SampleGallery from './SampleGallery';
import './css/tabs_semantic.css';
import PDFplaceholder from './images/PDFplaceholder.png'
import RightCardSinglePage from './RightCardSinglePage';
import axios from 'axios'
import placeholder from './images/placeHol.png'
import Loader from 'react-loader-spinner'
import LoadingOverlay from 'react-loading-overlay';

const Left = styled.div`
  display: inline-block;
  width : 49%;
  height : 100vh;
  max-height: 100vh; 
  overflow: hidden; 
  border: 1px solid #e9e9e9;
  background : #f8f9fa;
  margin-right : 1%;
`
const Right = styled.div`
  display: inline-block;
  margin-left : 1%;
  width : 49%;
  max-width: 49%;
  height : 100vh;
  max-height: 100vh;
  background : #f8f9fa; 
  border: 1px solid #e9e9e9;
  overflow: hidden;
`

class SinglePage extends React.Component {

    state = {
      image_dimensions : null,
      bounding_boxes :[],
      file: null,
      file_image_url: null,
      text_response: null,
      pdf: null,
      list_models : [],
      model_index:null,
      highlighted_box : -1,
      raw_text : "",
      text_resp_length : 0,
      loading: false,
    }

     componentDidMount(){
    }

     jsPdfGenerator = () => {
      // to download your pdf a file and at least 1 segmentation box are REQUIRED.
      if (this.state.file !== null && this.state.bounding_boxes.length){
        let template,scaled_image_values;
        
        if ( this.state.image_dimensions.width >= this.state.image_dimensions.height) {
          template = 'l'
          scaled_image_values = {'width' : 632, 'height' : this.state.image_dimensions.height*632/this.state.image_dimensions.width}
        }
        else {
          template = 'p'
          scaled_image_values = {'width' : 447, 'height' : this.state.image_dimensions.height*447/this.state.image_dimensions.width}
        }
        var doc = new jsPDF(template, 'pt',[scaled_image_values.width,scaled_image_values.height]);
        
        for (let i = 0; i<this.state.bounding_boxes.length;i++){
          let text = this.state.text_response[i].text
          let string_unit = doc.getStringUnitWidth(text)

          let new_width = this.state.bounding_boxes[i].width*scaled_image_values.width/this.state.image_dimensions.width
          let font_size = new_width/string_unit

          let new_x = this.state.bounding_boxes[i].x*scaled_image_values.width/this.state.image_dimensions.width
          let new_y = this.state.bounding_boxes[i].y*scaled_image_values.height/this.state.image_dimensions.height + this.state.bounding_boxes[i].height*scaled_image_values.height/this.state.image_dimensions.height
          doc.setFontSize(font_size)
          doc.text(text,new_x,new_y)
        }

        let mypdf = doc.output('bloburi')
        this.setState({pdf:mypdf})
      }
  }

  SaveImagePDF = () => {
    // to download your pdf a file and at least 1 segmentation box are REQUIRED.
    if (this.state.file !== null && this.state.bounding_boxes.length){
      let filename,template,scaled_image_values;
      if (this.state.file.name.indexOf(".png") > 0){
        filename = this.state.file.name.split(".png")[0]
      }
      else if (this.state.file.name.indexOf(".jpg") > 0){
        filename = this.state.file.name.split(".jpg")[0]
      } else filename = "YourPDF"
      
      if ( this.state.image_dimensions.width >= this.state.image_dimensions.height) {
        template = 'l'
        scaled_image_values = {'width' : 632, 'height' : this.state.image_dimensions.height*632/this.state.image_dimensions.width}
      }
      else {
        template = 'p'
        scaled_image_values = {'width' : 447, 'height' : this.state.image_dimensions.height*447/this.state.image_dimensions.width}
      }

      var doc = new jsPDF(template, 'pt',[scaled_image_values.width,scaled_image_values.height]);
      doc.setTextColor(0, 0, 0, 0);

      for (let i = 0; i<this.state.bounding_boxes.length;i++){
        let text = this.state.text_response[i].text
        let string_unit = doc.getStringUnitWidth(text)
        let new_width = this.state.bounding_boxes[i].width*scaled_image_values.width/this.state.image_dimensions.width
        let font_size = new_width/string_unit
        let new_x = this.state.bounding_boxes[i].x*scaled_image_values.width/this.state.image_dimensions.width
        let new_y = this.state.bounding_boxes[i].y*scaled_image_values.height/this.state.image_dimensions.height + this.state.bounding_boxes[i].height*scaled_image_values.height/this.state.image_dimensions.height
        doc.setFontSize(font_size)
        doc.text(text,new_x,new_y)
      }
      doc.addImage(this.state.file_image_url, "JPEG", 0, 0, scaled_image_values.width,scaled_image_values.height);
      doc.save(filename.concat('.pdf'))
    }
}

    onFileChange = (event) => {
      event.preventDefault();
      //let boxes_from_segmentation = [{ id: '1', x: 62, y: 67, width: 305, height: 39 },{ id: '2', x: 61, y: 109, width: 239, height: 34 },{ id: '3', x: 60, y: 148, width: 199, height: 41 }];
      //let text_in_boxes = [{ id : '1', text : 'ciao mamma guarda'},{ id : '2', text : 'come mi diverto'},{ id : '3', text : 'col canta tu'}];
      this.setState({
        file: event.target.files[0],
        bounding_boxes : [],
        //file_image_url: URL.createObjectURL(event.target.files[0])
      })
      /***base64 needed */
      let reader = new FileReader();
      reader.onloadend = () => {
        let image = new Image();
        image.src = reader.result
        image.onload = () => {
          this.setState({image_dimensions:{'width':image.width , 'height':image.height}})
        }
        this.setState({
          file_image_url: reader.result
        });
      }
      if (event.target.files.length !== 0 ) reader.readAsDataURL(event.target.files[0])
    }

    setBoxes = (items) =>{
      this.setState({bounding_boxes:items})
    }

  sendPage2HTR_new = (e) => {
    this.setState({loading:true})
    console.log('bounding: ', this.state.bounding_boxes)
    e.preventDefault();
    let form_data = new FormData();
    console.log(this.state.file)
    form_data.append('image', this.state.file);
    form_data.append('boxes', JSON.stringify(this.state.bounding_boxes))
    let url_predict = 'http://localhost:5050/predict'
    axios.post(url_predict, form_data, {
      headers: {
        'content-type': 'multipart/form-data',
      }
    })
        .then(response => {
          console.log(response)
          //this.setState({text_response: response.data.output})

          let lista = []
          for(let i=0; i<this.state.bounding_boxes.length; i++){
            let elem = {'id': this.state.bounding_boxes[i].id , 'text': response.data.predictions[i].prediction}
            lista.push(elem)
          }
          this.raw_text_update(lista)
          this.setState({text_resp_length:lista.length},() => this.setState({text_response: lista, loading: false}, this.jsPdfGenerator))
        })
        .catch(err => console.log(err), this.setState({loading:false}))
  };

    sendPage2HTR = (e) => {
      this.setState({loading:true})
      console.log('bounding: ', this.state.bounding_boxes)
      e.preventDefault();
      let form_data = new FormData();
      console.log(this.state.file)
      form_data.append('file', this.state.file);
      console.log('boxes', this.state.bounding_boxes)
      form_data.append('boxes', JSON.stringify(this.state.bounding_boxes))
      let url_predict = 'http://localhost:5025/ocr'
      //let url_predict = 'http://localhost:5025/predict-flor'
      //let url_predict = 'http://localhost:5000/predict'
      axios.post(url_predict, form_data, {
        headers: {
          'content-type': 'multipart/form-data',
        }
      })
          .then(response => {
            console.log(response)
            this.setState({text_response: response.data['predictions']})

            let lista = []
            for(let i=0; i<this.state.bounding_boxes.length; i++){
              let elem = {'id': this.state.bounding_boxes[i].id , 'text': response.data['predictions'][i]}
              lista.push(elem)
            }
            this.raw_text_update(lista)
            this.setState({text_resp_length:lista.length},() => this.setState({text_response: lista, loading: false})) //,this.jsPdfGenerator))
          })
          .catch(err => console.log(err), this.setState({loading:false}))
      };

    
    handleTabModelChange = (e, data) =>{
      this.setState({model_index : data.activeIndex})
    }

    updateTextResponse = (new_text_response) => {
      this.raw_text_update(new_text_response)
      this.setState({
        text_response:new_text_response ,
      }, this.jsPdfGenerator)
    }

    premilo = () => {
      let lisii = []
      this.state.bounding_boxes.forEach(box => lisii.push({"id":box.id,"text":"Ferdinando II"}) )
      this.raw_text_update(lisii)
      this.setState({text_resp_length:lisii.length},() => this.setState({text_response:lisii},this.jsPdfGenerator))
      
    }

    raw_text_update = (text) => {
      let string = ""
      for ( let i = 0 ; i<text.length;i++){
        string = string.concat(text[i].text)
        string = string.concat("\n")
      }
      this.setState({raw_text : string})
    }

    occamb = (event,data) =>{
      this.setState({raw_text:data.value})
    }

    render() {
      const images = [
        'https://2.bp.blogspot.com/-7jYnnTvygK4/UtyrdqBiuNI/AAAAAAAAGZ0/hsTP2C7UbuU/s1600/italian+handwriting16.jpg',
        'https://thumbs.dreamstime.com/b/vintage-italian-handwritten-text-24477630.jpg',
        '//placekitten.com/4000/3000',
      ];

      let list_models = []
      if (this.state.list_models.length !== 0){
        for(const [index,value] of this.state.list_models.entries()) {
          list_models.push(
            { menuItem: value.name, render: () => <Tab.Pane>
          <ul className="list-group">
            <li className="list-group-item"><h4>Language</h4><p>{value.lang}</p></li>
            <li className="list-group-item"><h4>Samples</h4><SampleGallery images={images}/></li>
            <li className="list-group-item"><h4>Description</h4><p>{value.desc}</p></li>
          </ul>
        </Tab.Pane> }
          )
        }
      }

      let right_panes = [
        {
          menuItem: 'Lines',
          pane: { 
            key: 'Lines',
            content: this.state.text_resp_length !== 0?  (
            
            <div className="right_single_page"><RightCardSinglePage
            text_lines = {this.state.text_response} 
            highlight_rect_on_start_text_edit = {id => this.setState({highlighted_box : id})}
            updateTextResponse={this.updateTextResponse} highlighted_box={this.state.highlighted_box} 
            /></div>) : (<div>
              <div >
                <img style={{width:"100%"}} className="img_placeholder" alt="" src={placeholder}></img>
              </div>
              </div>)
          },
        },
        {
          menuItem: 'PDF',
          pane: {
            key: 'tab2',
            content: this.state.pdf !== null ? (<PDFObject url={this.state.pdf} style={{height:"100vh"}} />):(<div>
              <div className="bbplaceholder " style={{marginTop:"100px"}}>
                <img className="img_placeholder_annotation" alt="" src={PDFplaceholder}></img>
              </div>
              <div className="text-center text_placeholder">
                <p>Output will be shown here</p>
              </div>
              </div>)
          },
        },
        {
          menuItem: 'Raw Text',
          pane: {
            key: 'tab3',
            content: <TextArea onChange={this.occamb} placeholder='Raw data output will appear here..' style={{ minHeight: "100%" , width:"100%", maxHeight: "100%"}} value={this.state.raw_text}/>
          },
        },
      ]

      let left_panes = [
        {
          menuItem: this.state.file !== null && this.state.file !== undefined ? this.state.file.name:'Tab 1',
          pane: { 
            key: 'tab1',
            content: <LeftCardSinglePage file_image_url = {this.state.file_image_url} setBoxes = {this.setBoxes}
           file={this.state.file}
          set_highlight_box_on_rect_click = {id => this.setState({highlighted_box : id})}
          highlighted_box = {this.state.highlighted_box}
          /> 
          },
        },
        {
          menuItem: 'Models',
          pane: {
            key: 'tab2',
            content: <Tab defaultActiveIndex="-1" onTabChange={this.handleTabModelChange} menu={{ fluid: true, vertical: true, tabular: true }} panes={list_models} />
          },
        },
      ]
      
      return (
        <div style={{textAlign:"center"}}>




    
    {/* Header */}
    <header className="bg-light py-5 mb-5">
    <div className="container h-100">
      <div className="row h-100 align-items-center">
        <div className=".col-6 .col-md-4">
          <h1 className="display-4 text-dark mt-5 mb-2">Single page HTR
            <button type="button" className="btn btn-link mt-3">Info</button>
          </h1>
          <p className ="text-secondary pt-4">Upload a document to visualize its text, starting the recognition using a ML model of your choice</p>
        </div>
        <div>
        <button type="button" className="btn btn-outline-dark ml-3 mr-2" onClick={this.SaveImagePDF}>Download Results</button>
        <button type="button" className="btn btn-outline-primary ml-3 mr-2" onClick={this.sendPage2HTR}>Send Page</button>

        <div className="file btn btn-primary position-relative overflow-hidden">
							Upload Document
							<input className="inputfile" type="file" onChange={this.onFileChange}>
              </input>
				</div>
        </div>
      </div>
    </div>
    </header>

{/* Body container  */}
<div className="containerone ">
<div>
  <Left style={{'marginBottom': '5vh'}}>
    <Tab className="myTab" panes={left_panes} renderActiveOnly={false} />
  </Left>

  <Right style={{'marginBottom': '5vh'}}>
    <Tab className="myTab" panes={right_panes} renderActiveOnly={false} />
  </Right>
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


</div>
      );
    }
  }
  
export { SinglePage };
