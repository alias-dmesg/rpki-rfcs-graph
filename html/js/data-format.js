(function() {
    packages = {
  
      // Lazily construct the package hierarchy from class names.
      root: function(classes) {
        var map = {};
  
        function find(name, data) {
          var node = map[name], i;
          if (!node) {
              node = map[name] = data || {name: name, children: []};
              if (name.length) {
              node.parent = find(name.substring(0, i = name.lastIndexOf(".")));
              node.parent.children.push(node);
              node.key = name.substring(i + 1);
              }
          } 
          return node;
        }
  
        
        nodes = []
        classes.forEach(function(d) {
            nodes.push({
              'name': d.from, 
              'kind': d.kind, 
              'source': d.from, 
              'target': d.to, 
              'color': d.color, 
              'title':d.title, 
              'group': d.group,
              'summary': d.summary})
        });

        nodes.forEach(function(d) {
          find(d.name, d);
        });
        
        return map[""];
      },
  
      // Return a list of imports for the given array of nodes.
      imports: function(nodes, classes) {
        var map = {},
            imports = [];
  
        // Compute a map from name to node.
        nodes.forEach(function(d) {
          map[d.name] = d;
        });

        // For each node, construct a link from the source to target node.
        classes.forEach(function(d) {
            if(d.from && d.to){
              imports.push({
                source: map[d.from], 
                target: map[d.to], 
                kind: d.kind, 
                color:d.color});
            }
        });
        return imports;
      }
  
    };
  })();