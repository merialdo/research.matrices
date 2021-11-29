import React from 'react';
/* import * as d3 from 'd3'
 */

class D3ExampleGraph extends React.Component{

    constructor(props){
        super()
        this.myRef = React.createRef();
        this.dataset = [100, 200, 300, 400, 500];
    }

    componentDidMount(){
        console.log(this.myRef)
        let size = 500;
        let svg = d3.select(this.myRef.current)
                    .append('svg')
                    .attr('width', size)
                    .attr('height', size);

        let rect_width = 95;
        svg.selectAll('rect')
                       .data(this.dataset)
                       .enter()
                       .append('rect')
                       .attr('x', (d, i) => 5 + i*(rect_width + 5))
                       .attr('y', d => size - d)
                       .attr('width', rect_width)
                       .attr('height', d => d)
                       .attr('fill', 'teal');

    }
    render(){
        return(
            <div ref={this.myRef}></div>
        )
    }
}

export default D3ExampleGraph;