import React from 'react'
import Dropzone from "react-dropzone"
import './css/thumb.css'; //css to better display input forms
import {Link} from 'react-router-dom';
import styled from 'styled-components';


const Header = styled.header`

    height : ${props =>{
        if (props.toggleHeigth === 0) return "300px"
        else return "300px"
    } }

`

const thumbsContainer = {
    display: 'flex',
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 16,
    maxHeight: 600,
    overflow: "auto"
  };

class DataPicker extends React.Component{

    constructor(props) {
        super(props);
        this.state = {
          files: [],
          data_other_viz : false,
        };

    }

    handleDrop = (acceptedFiles) => {

        let new_files = acceptedFiles.map(file => Object.assign(file, {
            preview: URL.createObjectURL(file)
        }))
        let files_in_grid = [...this.state.files, ...new_files]
        this.setState({ files: files_in_grid,
                        data_other_viz: true})
    }
    
    handleDelete = (e) =>{
        this.setState({files : this.state.files.filter(element => (element.name !==e.target.id))})
    }
    
    formatFilesForAnnotation = (files) => {
        var file_list = [];
        for (let i=0;i<files.length;i++){
          file_list.push({"filename":files[i].name,"file" : files[i], "file_url" : URL.createObjectURL(files[i]), "boxes" : [] , "max_id" : 1, "text_response" : [], "list_active_texts" : [], "is_confirmed": false,"index" : i, "is_in_test" : i%4 === 0 ? true : false })
        }
        return file_list   
       }
    
    render(){

        let MB = 0
        this.state.files.forEach(function(file){
            MB += file.size/1000000
        })

        const thumbs = this.state.files.map(file => (
            <div className='imagethumb' key={file.name}>
              <div className="thumbInner">
                <img
                  name='img'
                  src={file.preview}
                  className="img-fluid img-thumbnail"
                  alt = ""
                  ></img>
                <i 
                id = {file.name} 
                className="fa fa-times-circle fa-1x ico"
                aria-hidden="true"
                onClick={this.handleDelete}>
                </i>
              </div>
            </div>  
          ));

        const data_other_viz = this.state.data_other_viz
        
        return(
        <div>
            <Header toggleHeigth={this.state.files.length} className="bg-light py-5 mb-5">
                <div className="container h-100">
                    <div className="row h-100 align-items-center">
                        <div className="col-sm-6">
                            <h1 className="display-4 text-dark mt-5 mb-2">Data Staging Area
                            </h1>
                            
                            <h6 className ="text-secondary pt-4">
                                Create a <b>dataset</b> to <b>train your model</b>, upload your data and go to <b>annotation phase</b>
                            </h6>
                        </div>
                            <div className="col-sm-2"></div>
          
                        <div className="col-sm-4"> 
                            { data_other_viz && this.state.files.length ? (
                            <Link
                                to={{
                                pathname: "/annotationEditor",
                                state: { fromRedirect: this.formatFilesForAnnotation(this.state.files), datasetInfo: this.props.dataFromParent , is_from_creation:true}
                                }}
                            ><button className="btn btn-primary">Go to annotation editor</button></Link>
                            
                            ) : (null)}     
                            
                        </div>
                    </div>
                </div>
            </Header>


        { data_other_viz ? (
        <div className='container-fluid w-75'>
            <div className="row">
            {/* dataset info*/}
            <div className="col-4 ">
                <div className="card">
                    <div className="card-body">
                        <h6>Summary</h6>
                        <hr></hr>
                        <p className="card-text"><i className="fa fa-folder 2x" aria-hidden="true"></i>    Dataset Name:     {this.props.dataFromParent.dataset_name}</p>
                        <p className="card-text"><i className="fa fa-language 2x" aria-hidden="true"></i>    Language:     {this.props.dataFromParent.language}</p>
                        <p className="card-text"><i className="fa fa-list 2x" aria-hidden="true"></i>    number of files:     {this.state.files.length}</p>
                        <p className="card-text"><i className="fa fa-database 2x"></i>    dataset dimension in MB:    {MB.toPrecision(5)}</p>
                    </div>
                </div>
            </div>
            
            <div className="col-8 ">
                <div className="droparea">
                    <Dropzone onDrop={this.handleDrop}>
                        {({getRootProps, getInputProps}) => (
                            <section>
                                <div {...getRootProps()}>
                                    <input {...getInputProps()} />
                                    <p>Drag 'n' drop some files here, or click to select files</p>
                                </div>
                            </section>
                        )}
                    </Dropzone>
                </div>
                <div className="datapickergrid">
                    <aside style={thumbsContainer}>
                        {thumbs}
                    </aside>
                </div>  
            </div>
        </div>
    </div>)
        : 
        (
            <div className='container-fluid w-75'>
                <div className="row">
                    <div className="col md-8">

                            <div className="droparea">
                                <Dropzone onDrop={this.handleDrop}>
                                    {({getRootProps, getInputProps}) => (
                                    <section>
                                        <div {...getRootProps()}>
                                            <input {...getInputProps()} />
                                            <p>Drag 'n' drop some files here, or click to select files</p>
                                        </div>

                                    </section>
                                    )}
                                </Dropzone>
                            </div>
                    </div>
                </div>
            </div>
        )}
        </div>
        )
    }
}

export { DataPicker }