import React, { Component } from 'react';
import styled from 'styled-components';
import {
  ShapeEditor,
  ImageLayer,
  DrawLayer,
  wrapShape,
} from 'react-shape-editor';
import './css/rect.css';
import Loader from 'react-loader-spinner'
import LoadingOverlay from 'react-loading-overlay';
import PanZoom from "react-easy-panzoom";
import axios from 'axios'
import { Button } from 'semantic-ui-react';
import {FaHandPointer} from 'react-icons/fa';
import {FaSearchPlus} from 'react-icons/fa';
import {FaSearchMinus} from 'react-icons/fa';

const RectShape = wrapShape(({ width, height, scale, set_highlighted_rect_id, shapeIndex,highlighted_box }) => {
  const strokeWidth = 2 / scale;
  return (
    <rect
      width={Math.max(0, width - strokeWidth)}
      height={Math.max(0, height - strokeWidth)}
      x={strokeWidth / 2}
      y={strokeWidth / 2}
      fill={shapeIndex === highlighted_box && shapeIndex !== undefined ?"rgba(233, 244, 10, 0.3)": "rgba(0,255,255,0.3)"}
      stroke={shapeIndex === highlighted_box && shapeIndex !== undefined ?"rgba(233, 244, 10, 0.4)": "rgba(0,255,255,0.4)"}
      strokeWidth={strokeWidth}
      onClick={v=>set_highlighted_rect_id(shapeIndex)}
    />
  );
});


const MAX_FIT_SIZE = 550;
const MIN_SCALE = 0.05;
const MAX_SCALE = 4;

const to5 = n => Math.round(n);

const IssueWrapper = styled.div`
  padding: 3rem;
  max-width: 600px;
  margin: auto;
  white-space: pre-wrap;
`;

const Outer = styled.div`
  display: flex;
  height: 93vh;
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
`;


class LeftCardSinglePage extends Component {
  constructor(props) {
    super(props);

    this.state = {
        scale: 0.75,
        vectorWidth: 0,
        vectorHeight: 0,
        items : [],
        id : 1,
        file_image_url : null,
        loading: false,
        highlighted_box : -1,
        is_panning : false,
    };
    this.constrainMove = this.constrainMove.bind(this);
    this.constrainResize = this.constrainResize.bind(this);
  }

  componentDidUpdate(prevProps, prevState) {
    if (prevProps.file_image_url !== this.props.file_image_url){
        this.setState({
          file_image_url : this.props.file_image_url,
          items : [],
          id :1,
        });
    } 
    if(prevProps.highlighted_box !== this.props.highlighted_box){
      this.setState({highlighted_box : this.props.highlighted_box})
    }  
    if (JSON.stringify(prevState.items) !== JSON.stringify(this.state.items)){
        this.props.setBoxes(this.state.items)
    }
  }

  arrayReplace(arr, index, item) {
    return [
      ...arr.slice(0, index),
      ...(Array.isArray(item) ? item : [item]),
      ...arr.slice(index + 1),
    ];
  }

  constrainMove({ x, y, width, height }) {
    const { vectorWidth, vectorHeight } = this.state;
    return {
      x: to5(Math.min(vectorWidth - width, Math.max(0, x))),
      y: to5(Math.min(vectorHeight - height, Math.max(0, y))),
    };
  }

  constrainResize({ movingCorner: { x: movingX, y: movingY } }) {
    const { vectorWidth, vectorHeight } = this.state;
    return {
      x: to5(Math.min(vectorWidth, Math.max(0, movingX))),
      y: to5(Math.min(vectorHeight, Math.max(0, movingY))),
    };
  }
/*
  start_segmentation = () => {
    this.setState({loading:true});
    let file = this.props.file
      var bodyFormData = new FormData();
      bodyFormData.append('image', file);
      //console.log(this.state.file)
      let url = 'http://localhost:5005/predict-line';
      axios.post(url, bodyFormData, {
        headers: {
          //'accept': 'application/json',
          'content-type': 'multipart/form-data',
          //'Authorization': 'Bearer '+localStorage.getItem("access_token")
        }
      }).then(response => {
            var boxes_from_segmentation = response.data.segmentation
            boxes_from_segmentation.sort((el1,el2) => el1.y - el2.y)
            this.props.setBoxes(boxes_from_segmentation);
            this.setState({items: boxes_from_segmentation, id : boxes_from_segmentation.length+1,loading : false});
          })
          .catch(err => {console.log(err); this.setState({loading:false})})
  }*/

    start_segmentation = () => {
        this.setState({loading:true});
        let file = this.props.file
        var bodyFormData = new FormData();
        bodyFormData.append('file', file);
        let url = 'http://localhost:5015/mybiros/api/v1/text-detection/image/';
        axios.post(url, bodyFormData, {
            headers: {
                //'accept': 'application/json',
                'content-type': 'multipart/form-data',
                //'Authorization': 'Bearer '+localStorage.getItem("access_token")
            }
        }).then(response => {

            console.log(response)
            var boxes_from_segmentation = response.data['bounding_box']
            boxes_from_segmentation.sort((el1,el2) => el1.y - el2.y)
            this.props.setBoxes(boxes_from_segmentation);
            this.setState({items: boxes_from_segmentation, id : boxes_from_segmentation.length+1,loading : false});
        })
            .catch(err => {console.log(err); this.setState({loading:false})})


        //console.log(this.state.file)
        /*
        let url = 'http://localhost:5005/predict-line';
        axios.post(url, bodyFormData, {
          headers: {
            //'accept': 'application/json',
            'content-type': 'multipart/form-data',
            //'Authorization': 'Bearer '+localStorage.getItem("access_token")
          }
        }).then(response => {
              var boxes_from_segmentation = response.data.segmentation
              boxes_from_segmentation.sort((el1,el2) => el1.y - el2.y)
              this.props.async_set_segmentation_boxes(index_file,boxes_from_segmentation);
              this.setState({items: boxes_from_segmentation, id : boxes_from_segmentation.length+1,loading : false});
              this.props.enableGallery();
            })
            .catch(err => {console.log(err); this.props.enableGallery(); this.setState({loading:false})})*/
    }

  set_highlighted_rect_id = (ID) =>{
   if( this.state.highlighted_box !== ID) this.setState({highlighted_box : ID},() => {this.props.set_highlight_box_on_rect_click(ID)}) 
  }
/*********************************************************************************** */
  render() {
    const changeScale = ratio =>
      this.setState(state => ({
        scale: Math.max(MIN_SCALE, Math.min(MAX_SCALE, state.scale * ratio)),
      }));
    const { scale, vectorWidth, vectorHeight } = this.state;


    if (this.state.file_image_url === null) {
      return (
        <IssueWrapper>
          <div className="text_placeholder">Please Upload an image</div>
        </IssueWrapper>
      );
    }

    const shapes = this.state.items.map((item, index) => {
    const { id, height, width, x, y } = item;
       return (
        <RectShape
          // eslint-disable-next-line react/no-array-index-key
          key={id}
          highlighted_box = {this.state.highlighted_box}
          set_highlighted_rect_id = {this.set_highlighted_rect_id}
          constrainMove={this.constrainMove}
          constrainResize={this.constrainResize}
          height={height}
          onBlur={()=>this.setState({highlighted_box:-1},() => {this.props.set_highlight_box_on_rect_click(-1)})}
          keyboardTransformMultiplier={5}
          onChange={newRect => {
            let newArrayofItems = this.arrayReplace(this.state.items, index ,{
                ...item,
                ...newRect,
              })
              this.setState({
                items:newArrayofItems.sort((a, b) => a.y-b.y)
            })
          }
          }
          onDelete={() => {
            let newArrayofItems = this.arrayReplace(this.state.items, index, []);
            this.setState({items:newArrayofItems})
          }}
          ResizeHandleComponent = {(_a) => {
            var active = _a.active, cursor = _a.cursor, isInSelectionGroup = _a.isInSelectionGroup, onMouseDown = _a.onMouseDown, recommendedSize = _a.recommendedSize, scale = _a.scale, x = _a.x, y = _a.y;
            return (React.createElement("rect", { fill: active ? 'rgba(229,240,244,1)' : 'rgba(229,240,244,0)', height: recommendedSize, stroke: active ? 'rgba(53,33,140,1)' : 'rgba(53,33,140,0)', strokeWidth: 1 / scale , style: { cursor: cursor, opacity: isInSelectionGroup ? 0 : 1 }, width: recommendedSize, x: x - recommendedSize / 2  , y: y - recommendedSize / 2 , 
                // The onMouseDown prop must be passed on or resize will not work
                onMouseDown: onMouseDown }));
          }}
          shapeId={String(id)}
          shapeIndex={id}
          width={width}
          x={x}
          y={y}
        />
      );
    });

    return (
      <div>
      <Outer>
      <Toolbar >
      
      <Button basic compact onClick={() => changeScale(Math.sqrt(1.25))}><FaSearchPlus/></Button>
      <Button basic compact onClick={() => changeScale(1 / Math.sqrt(1.25))}><FaSearchMinus/></Button>
      
      <Button basic compact onClick={this.start_segmentation}>Segmentation</Button>
      
      <Button basic id ="botn" toggle active ={this.state.is_panning=== false} compact onClick={()=>this.setState({is_panning:false})}><i className="fa fa-mouse-pointer" ></i></Button>
      <Button basic id ="botn" toggle active ={this.state.is_panning === true} compact onClick={()=>this.setState({is_panning:true})}><FaHandPointer/></Button>
      
      </Toolbar>
        <Container>
        <PanZoom disableKeyInteraction disableDoubleClickZoom disableScrollZoom disabled={this.state.is_panning === false}>
          
          <InnerContainer style={{ width: vectorWidth * scale }}>
          <LoadingOverlay
            active={this.state.loading}
            spinner={<Loader
              type="Grid"
              color="#00BFFF"
              height={100}
              width={100}
           />}
          >
            <ShapeEditor
              scale={scale}
              vectorWidth={vectorWidth}
              vectorHeight={vectorHeight}
              style={{  pointerEvents: this.state.is_panning?'none':'auto', display: 'block' , boxShadow : ' 0 1rem 3rem rgba(0,0,0,.175)'}}
            >
              <ImageLayer
                src={this.state.file_image_url}
                onLoad={({ naturalWidth, naturalHeight }) => {
                  this.setState({
                    vectorWidth: naturalWidth,
                    vectorHeight: naturalHeight,
                    scale: MAX_FIT_SIZE / Math.max(naturalWidth, naturalHeight),
                  });
                }}
              />

              <DrawLayer
                constrainMove={this.constrainMove}
                constrainResize={this.constrainResize}
                DrawPreviewComponent={RectShape}
                onAddShape={({ x, y, width, height }) => {
                    this.setState(state => {
                      const items_befor_sort = state.items.concat({id : state.id.toString() ,x, y, width, height});
                      var items = items_befor_sort.sort((a, b) => a.y-b.y);
                      return {
                        items,
                        id : this.state.id+1
                      };
                    });
                  }}
              />
              {shapes}
            </ShapeEditor>
            </LoadingOverlay>
          </InnerContainer>
          </PanZoom>
        </Container>
      </Outer>
      </div>
    );
  }
}

export {LeftCardSinglePage};