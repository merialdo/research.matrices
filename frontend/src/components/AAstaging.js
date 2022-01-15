import React from 'react'
import Dropzone from "react-dropzone"
import './css/thumb.css'; //css to better display input forms
import {Link} from 'react-router-dom';
import styled from 'styled-components';
import { Tab } from 'semantic-ui-react';
import SampleGallery from './SampleGallery';

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

class MultiPageStaging extends React.Component{

    constructor(props) {
        super(props);
        this.state = {
          files: [],
          data_other_viz : false,
          list_models : [],
          model_index:null,
        };

    }

    componentDidMount(){
      }


    handleDrop = (acceptedFiles) => {

        let new_files = acceptedFiles.map(file => Object.assign(file, {
            preview: URL.createObjectURL(file)
        }))
        let files_in_grid = [...this.state.files, ...new_files]
        this.setState({ files: files_in_grid})
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
    
    handleTabModelChange = (e, data) =>{
        this.setState({model_index : data.activeIndex})
    }

    render(){

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

        
        return(
        <div>
            <Header toggleHeigth={this.state.files.length} className="bg-light py-5 mb-5">
                <div className="container h-100">
                    <div className="row h-100 align-items-center">
                        <div className="col-sm-6">
                            <h1 className="display-4 text-dark mt-5 mb-2">Upload the collection
                            </h1>
                            
                            <h6 className ="text-secondary pt-4">
                                Upload the collection of images for <b>Handwritten Text Recognition.</b>
                            </h6>
                        </div>
                            <div className="col-sm-2"></div>
          
                        <div className="col-sm-4"> 
                            { this.state.files.length ? (
                            <Link
                                to={{
                                pathname: "/multiPage",
                                state: { fromRedirect: this.formatFilesForAnnotation(this.state.files), datasetInfo: this.props.dataFromParent , is_from_creation:true}
                                }}
                            ><button className="btn btn-primary">Proceed</button></Link>
                            
                            ) : (null)}     
                            
                        </div>
                    </div>
                </div>
            </Header>


        
        <div className='container-fluid w-75'>
            <div className="row">
            {/* dataset info*/}
            <div className="col-6 ">
            
                <div className="card">
                    <div className="card-body">
                    <h1>Select a Model</h1>
                    <br></br>
                    <Tab defaultActiveIndex="-1" onTabChange={this.handleTabModelChange} menu={{ fluid: true, vertical: true, tabular: true }} panes={list_models} />
                    </div>
                </div>
            </div>
            
            <div className="col-6 ">
                <div className="droparea">
                    <Dropzone onDrop={this.handleDrop}>
                        {({getRootProps, getInputProps}) => (
                            <section>
                                <div {...getRootProps()}>
                                    <input {...getInputProps()} />
                                    <h3>Drag 'n' drop some files here, or click to select files</h3>
                                    <br/>
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
        )
    }
}

export { MultiPageStaging }