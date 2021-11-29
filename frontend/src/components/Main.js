import React from 'react';
import { Switch, Route } from 'react-router-dom';
import { Home } from './Home';
import Login from './Login';
import UserDashboard from './UserDashboard'
import { SinglePage } from './SinglePage';
import { CreateDataset } from './CreateDataset';
import {AnnotationEditor} from './AnnotationEditor';
//import {AnnoNEW} from './AnnoNEW';
import {CreateModel} from './CreateModel';
import {MultiPageStaging} from './AAstaging';
import {MultiPageEditor} from './AAeditor';

const Main = () => {
    return (
        <Switch>
            <Route exact path='/' component={Home}></Route>
            <Route exact path='/login' component={Login}></Route>
            <Route exact path="/UserDashboard" component={UserDashboard}></Route>
            <Route exact path='/singlePage' component={SinglePage}></Route>
            <Route exact path='/CreateDataset' component={CreateDataset}></Route>
            <Route exact path='/annotationEditor' component={AnnotationEditor}></Route>
            <Route exact path='/createModel' component={CreateModel}></Route>
            <Route exact path='/multiPageStaging' component={MultiPageStaging}></Route>
            <Route exact path='/multiPage' component={MultiPageEditor}></Route>
        </Switch>
    );
}

export { Main };
