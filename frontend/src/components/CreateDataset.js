import React from 'react'
import { CreateDatasetForm } from './CreateDatasetForm'
import { DataPicker } from './DataPicker'
import { Footer } from './Footer'

class CreateDataset extends React.Component{

    constructor(props) {
        super(props);
        this.state = {
          //dataset info
          dataset_name: null,
          language : null,
          description : null,
          // if true render data picker
          dataset_attributes_insterted: false,
          files : [],
        };
    }

    getModelDataForm = (childData) => {
        this.setState({
            dataset_name : childData.dataset_name,
            language: childData.language,
            description : childData.description,
            dataset_attributes_insterted : true,
        })
    }
    
    render(){

       let dataset_attributes_insterted = this.state.dataset_attributes_insterted /** TRUE: render DataPicker view, FALSE:render Create Model Info view */
  
        return(
        <div>

            { !dataset_attributes_insterted ? 
            (
                <CreateDatasetForm 
                modelDataFormCallback = {this.getModelDataForm}>
                </CreateDatasetForm>
            )
            :
            (
                <DataPicker dataFromParent={this.state}>
                </DataPicker>
            )
            }

            <Footer />


        </div>
        )
    }
}

export { CreateDataset }