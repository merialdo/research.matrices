import React, { Component } from 'react';
import styled from 'styled-components';
import './css/rect.css';
import Loader from 'react-loader-spinner'
import LoadingOverlay from 'react-loading-overlay';
import PanZoom from "react-easy-panzoom";
import axios from 'axios'
import { Button } from 'semantic-ui-react';
import {FaHandPointer} from 'react-icons/fa';
import { ReactPictureAnnotation } from "react-picture-annotation";
import {FaCompress} from 'react-icons/fa';

const MAX_FIT_SIZE = 1200;
const MIN_SCALE = 0.05;
const MAX_SCALE = 4;


const IssueWrapper = styled.div`
  padding: 3rem;
  max-width: 600px;
  margin: auto;
  white-space: pre-wrap;
`;

const Outer = styled.div`
  display: flex;
  height: 100vh;
  flex-direction: column;
`;

const Toolbar = styled.div`
  flex: 0 1 auto;
  border-bottom: solid gray 0px;
  padding: 5px 10px;
  background: #f8f9fa;
`;

const Container = styled.div`
  text-align: center;
  flex: 1 1 auto;
  width: 100%;
  overflow: auto;
  background: #ffffff;
`;

const InnerContainer = styled.div`
  position: relative;
  margin: auto;
  box-shadow : 0 1rem 3rem rgba(0,0,0,.175);
`;

class AnnotateOnPic extends Component {
  constructor(props) {
    super(props);
    this.myRef = React.createRef();
    this.state = {
        scale: 3.5,
        vectorWidth: 0,
        vectorHeight: 0,
        imageUrl : null,
        loading: false,
        is_panning : false,
        annotatio: [],
    };
  }

  componentDidUpdate(prevProps, prevState) {
    if (prevProps.active_file !== this.props.active_file){
        let image = new Image();
        image.src = this.props.active_file.file_url
        image.onload = () => {
            this.setState({
                annotatio : this.props.active_file.boxes,
                imageUrl : this.props.active_file.file_url,
                vectorWidth:image.width, 
                vectorHeight:image.height , 
                scale: MAX_FIT_SIZE / Math.max(image.width, image.height)})
        }
    }
  }

  start_segmentation = () => {
    this.props.disableGallery();
    this.setState({loading:true});
    const index_file =this.props.active_file.index
    let file = this.props.active_file.file
      var bodyFormData = new FormData();
      bodyFormData.append('image', file);
      //console.log(this.state.file)
      let url = 'http://localhost:5005/predict-line';
      axios.post(url, bodyFormData, {
        headers: {
          'content-type': 'multipart/form-data',
        }
      }).then(response => {
            var boxes_from_segmentation = response.data.segmentation
            boxes_from_segmentation.sort((el1,el2) => el1.y - el2.y)
            this.props.async_set_segmentation_boxes(index_file,boxes_from_segmentation);
            this.setState({items: boxes_from_segmentation, id : boxes_from_segmentation.length+1,loading : false});
            this.props.enableGallery(); 
          })
          .catch(err => {console.log(err); this.props.enableGallery(); this.setState({loading:false})})
  }

  
  onZoomIn =()=> {
    this.myRef.current && this.myRef.current.zoomIn(2)
  }

  onZoomOut =()=> {
    this.myRef.current && this.myRef.current.zoomOut(2)
  }

  reset = () =>{
    this.myRef.current && this.myRef.current.reset()
  }

  setAnnotation = (data) =>{
    this.setState({annotatio:data})
    this.props.updateAnnotatio(data)
  }
/*********************************************************************************** */
  render() {
    const changeScale = ratio =>
      this.setState(state => ({
        scale: Math.max(MIN_SCALE, Math.min(MAX_SCALE, state.scale * ratio)),
      }));
    const { scale, vectorWidth, vectorHeight} = this.state;


    if (this.state.imageUrl === null) {
      return (
        <IssueWrapper>
          <div className="text_placeholder">Please select an image in the gallery</div>
        </IssueWrapper>
      );
    }

    return (
      <div >
      <Outer>
      <Toolbar >
      
      <button type="button" className="btn btn-light" onClick={this.onZoomOut}>
        <i className="fa fa-search-minus fa-2"></i></button>
      
      <button type="button" className="btn btn-light" onClick={this.onZoomIn}>
      <i className="fa fa-search-plus fa-2"></i>
      </button>
      
      <button  className="btn btn-light" type="button" onClick={this.start_segmentation}>
        start segmentation
      </button>
      
      <Button basic id ="botn" toggle active ={this.state.is_panning=== false} compact onClick={()=>this.setState({is_panning:false})}><i className="fa fa-mouse-pointer" ></i></Button>
      <Button basic id ="botn" toggle active ={this.state.is_panning === true} compact onClick={()=>this.setState({is_panning:true})}><FaHandPointer/></Button>
      <Button basic id ="botn" compact onClick={this.reset}><FaCompress/></Button>
      </Toolbar>
        <Container>
        <PanZoom ref={this.myRef} disableKeyInteraction disableDoubleClickZoom disableScrollZoom disabled={this.state.is_panning === false}>
      
          <InnerContainer style={{ width: vectorWidth*scale }}>
          <LoadingOverlay
            active={this.state.loading}
            spinner={<Loader
              type="Grid"
              color="#00BFFF"
              height={100}
              width={100}
           />}
          >
        <div style={{ width:vectorWidth*scale, height:vectorHeight*scale, pointerEvents: this.state.is_panning?'none':'auto', display: 'block' , boxShadow : ' 0 1rem 3rem rgba(0,0,0,.175)'}}>
        <ReactPictureAnnotation
        annotationData={this.state.annotatio}
        image={this.state.imageUrl}
        onSelect={(selectedId)=>console.log(selectedId)}
        onChange={this.setAnnotation}
        width={this.state.vectorWidth*this.state.scale}
        height={this.state.vectorHeight*this.state.scale}
      />
        </div>
            </LoadingOverlay>
          </InnerContainer>
          </PanZoom>
        </Container>
      </Outer>
      </div>
    );
  }
}

export {AnnotateOnPic};