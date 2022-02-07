import React, {Component} from 'react';
import EdiText from 'react-editext';
import styled from 'styled-components'
import update from 'immutability-helper'; 
import { Button } from 'semantic-ui-react';
import './css/filter.css';
const TO_ANNOTATE = 'TO ANNOTATE!!!'


const StyledEdiText = styled(EdiText)`
button[editext='edit-button']{
    text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 12px;
  
}

  button[editext='save-button'] {
    text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 12px;
   
  }
  button[editext='cancel-button'] {
    text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 12px;
   
  }
  div[editext='view-container'] {
    transition: border-left,background 0.3s ease-in-out;
    font-size: 14px;
    border-left:  ${props => {
      const is_new_box_bool = props.active.includes(props.text_id)
      if (props.highlighted_box === props.text_id || props.highlighted_box.toString().localeCompare(props.text_id) === 0 ){
        return '5px solid #007bff';
      }
      if (is_new_box_bool) {
        return '5px solid #ffb1b1';
      }
      else return '5px solid #A9A9A9';
    }};   
    border-bottom: 2px solid #d3d3d3;
    font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
    font: bold;
    width : 100%;
    height:25px;
    padding: 25px; 
    background: ${props => {
      if (props.highlighted_box === props.text_id || props.highlighted_box.toString().localeCompare(props.text_id) === 0){
        return 'rgba(233, 244, 10, 0.2)';
      }
      
    }};
    &:hover {
        border-left: 5px solid #007bff; 
        background: rgba(0, 255, 255, 0.1);
      }
    }
  div[editext='edit-container'] {
  transition: border-left,background 0.3s ease-in-out;
  font-size: 14px;
  font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
  font: bold;
  border-left:  ${props => {
    if (props.highlighted_box === props.text_id || props.highlighted_box.toString().localeCompare(props.text_id) === 0 || props.now_editing === props.text_id){
      return '5px solid #007bff';
    }
    else return '5px solid #A9A9A9';
  }};  
  border-bottom: 2px solid #d3d3d3;
  width : 100%;
    height:25px;
    padding: 25px;
    background: ${props => {
      if (props.highlighted_box === props.text_id || props.highlighted_box.toString().localeCompare(props.text_id) === 0){
        return 'rgba(233, 244, 10, 0.2)';
      }
      return 'rgba(0, 0, 0, 0)';
      }
    }};
  }
`

export default class TextEditor extends Component {
    state = {
        text_line_objects : null,
        list_active_texts : "-1",
        now_editing : null,
        highlighted_box : -1
    }
    componentDidUpdate(prevProps, prevState){
        if (prevProps.text_lines !== this.props.text_lines){
            this.setState({text_line_objects : this.props.text_lines})
        }
        if (prevProps.highlighted_box !== this.props.highlighted_box){
          this.setState({highlighted_box : this.props.highlighted_box})
        }
        if (prevProps.list_active_texts !== this.props.list_active_texts){
          this.setState({list_active_texts : this.props.list_active_texts})
        }
    }
//in the following we update "text_response" in Annotation editor. 
    updateTextAfterSave( ID, new_text ) {
      let text_response = this.state.text_line_objects
      for (var i in text_response) {
        if (text_response[i].id === ID) {
           text_response[i].text = new_text;
           break; 
        }
      }
     this.props.updateTextResponse(text_response)//callback here
   }

    handleSave = (val, inputProps) => {
        this.updateTextAfterSave(this.state.now_editing, val)
        this.props.highlight_rect_on_start_text_edit(-1)
         
        if ( val.localeCompare("") !== 0){
          let old_list = this.state.list_active_texts
          let index = old_list.indexOf(this.state.now_editing);
          if (index !== -1) old_list.splice(index, 1);
          this.setState({list_active_texts:old_list})
        }
      }

    setActiveBox (id,v) {
       if (v.localeCompare(TO_ANNOTATE) === 0) {
         let found = this.state.text_line_objects.find(element => element.id === id)
         let index = this.state.text_line_objects.findIndex(element => element === found)
         this.setState({
          text_line_objects: update(this.state.text_line_objects, {[index]: {text : {$set: ""}}}),
        })
       }
       this.props.highlight_rect_on_start_text_edit(id)
       this.setState({now_editing : id})
    }



    confirm = () => {
      if ( this.state.list_active_texts.length > 0) alert("some annotations need review!")
      else this.props.set_confirmation()
    }

    deleteLine =(id) =>{
      this.setState({text_line_objects:this.state.text_line_objects.filter(obj=>{return obj.id !== id})})
      this.props.deleteTextLine(id)
    }

    render(){
        let left_card_body = ''
        if (this.state.text_line_objects !== null){
        left_card_body = this.state.text_line_objects.map((d) => { 
            return <div key = {d.id} style={{ padding: 5 }}>
            <StyledEdiText
            key = {d.id}
            text_id = {d.id}
            now_editing ={this.state.now_editing}
            hideIcons={true}
            cancelButtonContent={<i className="fa fa-trash"></i>}
            saveButtonContent={<i className="fa fa-check"></i>}
            editButtonContent={<i className="fa fa-pencil"></i>}
            editButtonClassName={"btn btn-outline-primary"}
            cancelButtonClassName={"btn btn-outline-primary"}
            saveButtonClassName={"btn btn-outline-primary"}
            editOnViewClick={true}
            submitOnUnfocus
            submitOnEnter
            highlighted_box = {this.state.highlighted_box}
            active = {this.state.list_active_texts}
            showButtonsOnHover
            onEditingStart={v =>
                this.setActiveBox(d.id,v)
              }
            value={d.text}
            onSave={this.handleSave}
            onCancel={v=>this.deleteLine(d.id)}
            cancelOnEscape = {true}
          />
          </div>});
        }
        return (
            <div>
              <div className="sticky-button-confirm" style={{background:"#f8f9fa",marginBottom:"1vh",marginTop:"1vh"}}><Button id="confirm" compact basic onClick={this.confirm}>Confirm Current File Annotation</Button></div>
                {left_card_body}
            </div>
        );
    };

}