Here is a simple memory-optimized C++ program using Depth-First Search (DFS) approach on Graphs, which uses recursion:

```cpp
#include<bits/stdc++.h>
using namespace std;

class Graph {
    int V;
    list<int> *adj;
public:
    Graph(int V);
    void addEdge(int v, int w);
    void DFSUtil(int v, bool visited[]);
    void DFS();
};

Graph::Graph(int V) {
    this->V = V;
    adj = new list<int>[V];
}

void Graph::addEdge(int v, int w) {
    adj[v].push_back(w);
}

void Graph::DFSUtil(int v, bool visited[]) {
    visited[v] = true;
    cout << v << " ";

    for (int i = 0; i < adj[v].size(); ++i)
        if (!visited[adj[v][i]])
            DFSUtil(adj[v][i], visited);
}

void Graph::DFS() {
    bool *visited = new bool[V];
    for (int i = 0; i < V; i++)
        visited[i] = false;

    for (int i = 0; i < V; i++)
        if (!visited[i])
            DFSUtil(i, visited);
}

int main(){
    Graph g(4);
    g.addEdge(0, 1);
    g.addEdge(0, 2);
    g.addEdge(1, 2);
    g.addEdge(2, 0);
    g.addEdge(2, 3);
    g.addEdge(3, 3);

    cout << "Following is Depth First Traversal (starting from vertex 2) \n";
    g.DFS();

    return 0;
}
```

[PASS]