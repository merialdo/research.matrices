import React from 'react';
import './css/Input.css';
import {Editor} from './Editor';
import TextEditor from './TextEditor';
import update from 'immutability-helper';
import boundingbox_placeholder from './images/boundingbox_grey.png';
import {Button} from 'semantic-ui-react';
import './css/filter.css';
import axios from 'axios';
import {FaSave} from 'react-icons/fa'

import styled from 'styled-components';

const Left = styled.div`
  display: inline-block;
  width: ${props => {
    if (props.toggleLeft === true && props.toggleRight === true) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false) return "0%"
    if (props.toggleLeft === false && props.toggleRight === true) return "50%"
    else return "25%"
  }};
  max-width: ${props => {
    if (props.toggleLeft === true && props.toggleRight === true) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false) return "0%"
    if (props.toggleLeft === false && props.toggleRight === true) return "50%"
    else return "25%"
  }};
  height: 100vh;
  max-height: 100vh;
  background: #f8f9fa;
  overflow: auto;
  border: ${props => {
    if (props.toggleLeft === true && props.toggleRight === true) return "0px "
    if (props.toggleLeft === true && props.toggleRight === false) return "0px "
    else return "1px solid #f8f9fa"
  }};
`
const Right = styled.div`
  display: inline-block;
  width: ${props => {
    if (props.toggleRight === true && props.toggleLeft === true) return "0%"
    if (props.toggleRight === true && props.toggleLeft === false) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false) return "25%"
    else return "25%"
  }};
  max-width: ${props => {
    if (props.toggleRight === true && props.toggleLeft === true) return "0%"
    if (props.toggleRight === true && props.toggleLeft === false) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false) return "50%"
    else return "25%"
  }};
  height: 100vh;
  max-height: 100vh;
  background: #f8f9fa;
  overflow: auto;
  border: ${props => {
    if (props.toggleRight === true && props.toggleLeft === true) return "0px "
    if (props.toggleRight === true && props.toggleLeft === false) return "0px "
    else return "1px solid #f8f9fa"
  }};
`
const Center = styled.div`
  display: inline-block;
  width: ${props => {
    if (props.toggleLeft === true && props.toggleRight === true) return "100%"
    if (props.toggleLeft === true && props.toggleRight === false) return "75%"
    else return "50%"
  }};
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
  border: 1px solid #f8f9fa;
`
const Frame = styled.div`
  width: ${props => {
    if (props.toggleLeft === true && props.toggleRight === true) return "0%"
    if (props.toggleLeft === true && props.toggleRight === false) return "0%"
    if (props.toggleLeft === false && props.toggleRight === true) return "25%"
    else return "50%"
  }};
  height: 150px;
  border: 1px solid #f8f9fa;
  transition: all 0.3s ease;
  text-align: center;

  &:hover {
    background: #FFFFFF;
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
      if (props.active_id === props.personal_index) {
        return " 5px -5px 0px #007bff";
      } else return " 5px -5px 0px  #A9A9A9;";
    }};
  }

  box-shadow: ${props => {
    if (props.active_id === props.personal_index) {
      return " 5px -5px 0px #007bff";
    } else return " 5px -5px 0px rgba(0,0,0,0)";
  }};
`
const Icon = styled.i`
  position: absolute;
  bottom: 5px;
  transition: all 0.3s ease-in-out;
  left: 5px;
  color: ${props => {
    if (props.is_confirmed) return "#7cfc00";
    if (props.list_length > 0) {
      return "#ffae1a";
    } else return "rgba(0,0,0,0)";
  }};
`

const TO_ANNOTATE = 'TO ANNOTATE!!!'

class AnnotationEditor extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            toggleLeft: false,
            toggleRight: false,
            index_active_file_in_files: null,
            files: this.props.location.state.fromRedirect.sort((a, b) => parseFloat(a.index) - parseFloat(b.index)),
            active_file: null,
            highlighted_box: -1,
            list_length: 0,
            filter: 0,
            disabled: false,
            dataset_name: /* this.props.location.state.datasetInfo.dataset_name ? this.props.location.state.datasetInfo.dataset_name :  */this.props.location.state.dataset_name,
            dataset_id: this.props.location.state.dataset_id,
            is_from_creation: this.props.location.state.is_from_creation,
            is_save_disabled: false,
            gt_file: null,
        }
    }

    componentDidMount() {
        console.log('location', this.props.location.state);
    }/*
    componentDidUpdate(prevProps, prevState) {
      console.log(this.state.files)
    }*/

    handleAddBox = (lista_id, new_boxes, max_id) => {
        let new_text_response = []
        let newID = []
        for (let i = 0; i < lista_id.length; i++) {
            let ID = lista_id[i]
            var elem = {}
            var result = this.state.files[this.state.index_active_file_in_files].text_response.filter(obj => {
                return obj.id === ID
            })
            if (result.length > 0 && result[0].text.localeCompare(TO_ANNOTATE) !== 0 && result[0].text.localeCompare("") !== 0) {
                new_text_response.push(result[0])
            } else {
                elem = {'id': ID, 'text': TO_ANNOTATE}
                new_text_response.push(elem)
                newID.push(ID)
            }
        }
        if (JSON.stringify(this.state.files[this.state.index_active_file_in_files].boxes) !== JSON.stringify(new_boxes)) {
            this.setState({list_length: new_text_response.length}, () =>
                this.setState({
                    files: update(this.state.files, {
                        [this.state.index_active_file_in_files]: {
                            boxes: {$set: new_boxes},
                            max_id: {$set: max_id},
                            text_response: {$set: new_text_response},
                            list_active_texts: {$set: newID},
                            is_confirmed: {$set: false}
                        }
                    }),
                }))
        } else {
            this.setState({list_length: new_text_response.length}, () =>
                this.setState({
                    files: update(this.state.files, {
                        [this.state.index_active_file_in_files]: {
                            boxes: {$set: new_boxes},
                            max_id: {$set: max_id},
                            text_response: {$set: new_text_response},
                            list_active_texts: {$set: newID}
                        }
                    }),
                }))
        }
    }

    sendPage2HTR = (e) => {
        e.preventDefault();
        let form_data = new FormData();
        form_data.append('file', this.state.active_file['file']);
        form_data.append('boxes', JSON.stringify(this.state.files[this.state.index_active_file_in_files]['boxes']))
        let url_predict = 'http://localhost:5025/ocr'
        axios.post(url_predict, form_data, {
            headers: {
                'content-type': 'multipart/form-data',
            }
        })
            .then(response => {
                console.log(response)
                let ocr_hints = []

                for (let i=0; i < this.state.files[this.state.index_active_file_in_files].list_active_texts.length; i++ ){
                    ocr_hints.push({'id': this.state.files[this.state.index_active_file_in_files].list_active_texts[i], 'text': response.data['predictions'][i]})
                }
                this.updateTextResponse(ocr_hints)
            })
            .catch(err => console.log(err), this.setState({loading: false}))

    };

    updateTextResponse = (new_text_response) => {
        console.log('new text response', new_text_response)
        console.log(this.state.files[this.state.index_active_file_in_files])



        this.setState({
            files: update(this.state.files, {[this.state.index_active_file_in_files]: {text_response: {$set: new_text_response}}}),
        })
    }

    updateGT = (new_text_response) => {
        console.log('upload gt', new_text_response)

        let text_response = []

        for (let i=1; i <= this.state.files[this.state.index_active_file_in_files]['boxes'].length; i++ ){
            text_response.push({'id': i, 'text': this.state.gt_file[i-1]})
        }
        this.updateTextResponse(text_response)

    }


    set_confirmation = () => {
        this.setState({
            files: update(this.state.files, {[this.state.index_active_file_in_files]: {is_confirmed: {$set: true}}}),
        })
    }

    togglefilter0 = () => {
        this.setState({filter: 0})
    }
    togglefilter1 = () => {
        this.setState({filter: 1})
    }
    togglefilter2 = () => {
        this.setState({filter: 2})
    }
    togglefilter3 = () => {
        this.setState({filter: 3})
    }

    filter_files = () => {
        const filter0 = this.state.files;
        const filter1 = this.state.files.filter(element => element.text_response.length === 0);
        const filter2 = this.state.files.filter(element => element.is_confirmed === false && element.text_response.length > 0);
        const filter3 = this.state.files.filter(element => element.is_confirmed === true);

        let filtered;
        if (this.state.filter === 0) filtered = filter0;
        if (this.state.filter === 1) filtered = filter1;
        if (this.state.filter === 2) filtered = filter2;
        if (this.state.filter === 3) filtered = filter3;
        return filtered;
    }

    async_set_segmentation_boxes = (index_file, boxes_from_segmentation) => {
        this.setState({
            files: update(this.state.files, {[index_file]: {boxes: {$set: boxes_from_segmentation}}}),
        })
    }

    deleteTextLine = (id) => {
        let new_boxes = this.state.files[this.state.index_active_file_in_files].boxes.filter(obj => {
            return obj.id !== id
        })
        this.setState({
            files: update(this.state.files, {
                [this.state.index_active_file_in_files]: {
                    boxes: {$set: new_boxes},
                    is_confirmed: {$set: false}
                }
            }),
        }, () => {
            this.setState({active_file: this.state.files[this.state.index_active_file_in_files]})
        })
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

    createSegmentationLine(files) {
        let segmentation_boxes = {}
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
            segmentation_boxes[name] = {"lines": boxes}
        }

        console.log('createSegmentationLine', segmentation_boxes)

        return segmentation_boxes

    }

    createDataset = () => {
        let form_data = new FormData();
        form_data.append('name', this.state.dataset_name)
        this.state.files.forEach(f => form_data.append(f.filename, f.file))

        let labels = this.createAnnotationsMongo(this.state.files)
        form_data.append('annotations', JSON.stringify(labels))

        let url = 'http://localhost:5000/api/dataset-creator';
        axios.post(url, form_data, {
            headers: {
                'content-type': 'multipart/form-data',
            }
        })
            .then(response => {
                console.log(response)
            })
            .catch(err => console.log(err))
    };


    createSegmentationDataset = () => {
        let form_data = new FormData();
        form_data.append('name', this.state.dataset_name)
        this.state.files.forEach(f => form_data.append(f.filename, f.file))

        let segmentation_boxes = this.createSegmentationLine(this.state.files)
        form_data.append('annotations', JSON.stringify(segmentation_boxes))

        console.log(form_data, this.state.dataset_name)

        let url = 'http://localhost:5000/api/segmentation-dataset-creator';
        axios.post(url, form_data, {
            headers: {
                'content-type': 'multipart/form-data',
            }
        })
            .then(response => {
                console.log(response)
            })
            .catch(err => console.log(err))
    };


    sendUpdateToServer = () => {
        this.setState({is_save_disabled: true})
        let form_data = new FormData();

        let labels = this.createAnnotationsMongo(this.state.files)
        form_data.append('annotations', JSON.stringify(labels))

        let url = 'http://localhost:5000/api/datasets/' + this.state.dataset_id;
        axios.put(url, form_data, {
            headers: {
                'content-type': 'multipart/form-data',
            }
        })
            .then(response => {
                console.log(response);
                this.setState({is_save_disabled: false})
                alert("Successfully updated your Dataset!")
            })
            .catch(err => {
                console.log(err)
                this.setState({is_save_disabled: false})
                alert("ERROR : couldn't update your Dataset!")
            })
    }

    sendDatasetToServer = () => {
        this.setState({is_save_disabled: true})
        let form_data = new FormData();
        form_data.append('name', this.props.location.state.datasetInfo.dataset_name)
        form_data.append('language', this.props.location.state.datasetInfo.language)
        this.state.files.forEach(f => form_data.append(f.file.name, f.file))

        let labels = this.createAnnotationsMongo(this.state.files)
        form_data.append('annotations', JSON.stringify(labels))

        let url = 'http://localhost:5000/api/datasets';
        axios.post(url, form_data, {
            headers: {
                'content-type': 'multipart/form-data',
            }
        })
            .then(response => {
                console.log(response)
                this.setState({
                    dataset_id: response.data.id,
                    is_save_disabled: false,
                    is_from_creation: false,
                })
                alert("Successfully saved your Dataset!")
            })
            .catch(err => {
                    console.log(err);
                    this.setState({is_save_disabled: false})
                    alert("ERROR : couldn't save your Dataset!")
                }
            )
    };

    handleGTChange = e => {
        console.log('handle file change:', e.target.files)
        if (e.target.files.length) {

            let gt_file = e.target.files[0]

            const reader = new FileReader()
            reader.onload = async (e) => {
                let text = (e.target.result)
                console.log(text)
                alert(text)

                text = text.split(/\r?\n/)
                this.setState({gt_file : text})
                this.updateGT()

            };
            reader.readAsText(gt_file)
        }

    };


    render() {
        const items = []

        let filtered = this.filter_files();
        if (this.state.files !== undefined) {
            for (const [index, value] of filtered.entries()) {
                items.push(
                    <Frame toggleLeft={this.state.toggleLeft} toggleRight={this.state.toggleRight} key={index}
                           className="frame" onClick={v => this.setState({
                        index_active_file_in_files: value.index,
                        active_file: filtered[index],
                        list_length: value.text_response.length
                    })}>
                        <span className="helper"></span><Img active_id={this.state.index_active_file_in_files}
                                                             personal_index={filtered[index].index} src={value.file_url}
                                                             alt=""/><Icon is_confirmed={value.is_confirmed}
                                                                           list_length={value.text_response.length}
                                                                           className="fa fa-check-circle"></Icon>
                    </Frame>)
            }
        }

        return (

            <div style={{textAlign: "center"}}>
                <br/>
                {/**
                 <br/>
                 <button className="btn btn-secondary" onClick={this.sendDatasetToServer}>Save state of annotation</button>
                 <button className="btn btn-secondary" onClick={this.sendUpdateToServer}>Update annotation</button>
                 <button className="btn btn-secondary" onClick={this.createDataset}>Create Dataset</button>
                 <br/>
                 */}
                {/* Body container  */}

                <div className="containerone ">

                    <div className="icon-bar-try">
                        <button onClick={() => {
                            this.setState({toggleLeft: !this.state.toggleLeft})
                        }} className="buttonVertical-try btn-primary">
                            <i className="fa fa-picture-o fa-1x ico"></i> Images
                        </button>
                    </div>
                    <div className="icon-bar-right-try">
                        <button onClick={() => {
                            this.setState({toggleRight: !this.state.toggleRight})
                        }} className="buttonVertical-try btn-primary">
                            <i className="fa fa-tag fa-1x ico"></i> Annotations
                        </button>
                    </div>

                    <div>
                        <Left style={{pointerEvents: this.state.disabled ? 'none' : 'auto'}}
                              toggleLeft={this.state.toggleLeft} toggleRight={this.state.toggleRight}>
                            <div className="container">

                                <div>
                                    <Button.Group basic widths="5">
                                        <Button id="botn" toggle active={this.state.filter === 0} compact
                                                onClick={this.togglefilter0}>All</Button>
                                        <Button id="botn" toggle active={this.state.filter === 1} compact
                                                onClick={this.togglefilter1}>To Do</Button>
                                        <Button id="botn" toggle active={this.state.filter === 2} compact
                                                onClick={this.togglefilter2}><i className="fa fa-check-circle"
                                                                                style={{color: "#ffae1a"}}></i> Doing</Button>
                                        <Button id="botn" toggle active={this.state.filter === 3} compact
                                                onClick={this.togglefilter3}><i className="fa fa-check-circle"
                                                                                style={{color: "#7cfc00"}}></i> Done</Button>
                                        <Button compact disabled={this.state.is_save_disabled}
                                                onClick={this.state.is_from_creation === true ? this.sendDatasetToServer : this.sendUpdateToServer}><FaSave
                                            style={{fontSize: "1.5vw"}}/></Button>
                                        <button className="btn btn-outline-primary" onClick={this.createDataset}>Export
                                            Dataset
                                        </button>
                                        {/*<button className="btn btn-secondary" onClick={this.createSegmentationDataset}>Create Seg Dataset</button>*/}

                                    </Button.Group>
                                </div>

                                <div className="row">
                                    {items.length ? items : null}
                                </div>
                            </div>
                        </Left>
                        <Center toggleLeft={this.state.toggleLeft} toggleRight={this.state.toggleRight}>
                            <Editor active_file={this.state.active_file}
                                    setSegmentationBoxes={this.setSegmentationBoxes}
                                    onAddBox={this.handleAddBox} highlighted_box={this.state.highlighted_box}
                                    set_highlight_box_on_rect_click={id => this.setState({highlighted_box: id})}
                                    set_text_response_from_segmentation={this.updateTextResponse}
                                    async_set_segmentation_boxes={this.async_set_segmentation_boxes}
                                    disableGallery={() => this.setState({disabled: true})}
                                    enableGallery={() => this.setState({disabled: false})}
                            />
                        </Center>

                        <Right toggleLeft={this.state.toggleLeft} toggleRight={this.state.toggleRight}>

                            <div className="sticky-button-confirm"
                                 style={{background: "#f8f9fa", marginBottom: "1vh", marginTop: "1vh"}}><Button
                                id="confirm" compact basic onClick={this.sendPage2HTR}>OCR Hint</Button></div>
                            <div className="sticky-button-confirm"
                                 style={{background: "#f8f9fa", marginBottom: "1vh", marginTop: "1vh"}}><input
                                type="file" compact basic onChange={this.handleGTChange}/>Upload
                                GT</div>


                            {this.state.list_length > 0 ? (
                                <TextEditor
                                    text_lines={this.state.files[this.state.index_active_file_in_files].text_response}
                                    list_active_texts={this.state.files[this.state.index_active_file_in_files].list_active_texts}
                                    highlight_rect_on_start_text_edit={id => this.setState({highlighted_box: id})}
                                    updateTextResponse={this.updateTextResponse}
                                    highlighted_box={this.state.highlighted_box}
                                    set_confirmation={this.set_confirmation}
                                    deleteTextLine={this.deleteTextLine}
                                />
                            ) : (
                                <div>
                                    <div className="bbplaceholder">
                                        <img className="img_placeholder_annotation" alt=""
                                             src={boundingbox_placeholder}></img>
                                    </div>
                                    <div className="text-center text_placeholder">
                                        <p>Draw your first bounding box in the editor</p>
                                    </div>
                                </div>
                            )}
                        </Right>

                    </div>
                </div>
            </div>
        );
    }
}

export {AnnotationEditor};
