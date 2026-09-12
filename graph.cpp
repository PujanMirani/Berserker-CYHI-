Here's a simple solution using Depth First Search (DFS) in a memory optimized manner:

```cpp
#include<iostream>
#include<vector>
using namespace std;

void DFS(vector<int> adj[], bool visited[], int V, int s)
{
    visited[s] = true;
    cout << s << " ";

    for(int i=0; i<adj[s].size(); i++)
        if(!visited[adj[s][i]])
            DFS(adj, visited, V, adj[s][i]);
}

void GraphTraversal(vector<int> adj[], int V)
{
    bool visited[V+1];
    
    for (int i = 0; i <= V; ++i)
        visited[i] = false;

    for (int i=1; i<=V; i++)
      if (!visited[i])
         DFS(adj, visited, V, i);
}

int main()
{
    int V = 5;
    vector<int> adj[V+1];

    // Adding edges to the graph
    adj[0] = {1,2};
    adj[1] = {3};
    adj[2] = {4};

    GraphTraversal(adj, V);

    return 0;
}
```

In this program, a Depth First Search (DFS) traversal is performed using a recursive function. A boolean array 'visited[]' is used to mark the vertices that have been visited so that they are not visited again.

The time complexity of DFS is O(V + E), where V is the number of vertices and E is the number of edges in the graph. Since we're visiting each vertex once, and looking at all its adjacent nodes, this implementation is efficient for competitive programming scenarios.

[FAIL]