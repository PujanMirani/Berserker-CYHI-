To write an efficient memory-optimized program, we can use either Breadth First Search (BFS) or Depth First Search (DFS). For simplicity and efficiency in terms of memory usage, we'll implement BFS using a queue data structure.

Here is a basic template that uses C++ STL:

```cpp
#include<bits/stdc++.h>
using namespace std;

vector<int> bfs(int n, vector<vector<int>>& adjList) {
    vector<bool> visited(n, false);
    queue<int> q;
    vector<int> result;

    // start from node 0
    visited[0] = true;
    q.push(0);

    while (!q.empty()) {
        int currNode = q.front();
        q.pop();

        result.push_back(currNode); // process the current node

        for (auto neighbor : adjList[currNode]) {
            if (!visited[neighbor]) {
                visited[neighbor] = true;
                q.push(neighbor);
            }
        }
    }

    return result;
}

int main() {
    int n, m; // number of nodes and edges
    cin >> n >> m;

    vector<vector<int>> adjList(n);

    for (int i = 0; i < m; i++) {
        int u, v;
        cin >> u >> v;
        // if the graph is undirected
        adjList[u].push_back(v);
        adjList[v].push_back(u);
    }

    vector<int> result = bfs(n, adjList);

    for (auto node : result) cout << node << " ";

    return 0;
}
```

This program reads in a number of nodes `n` and edges `m`, then reads the pairs of connected nodes. It constructs an adjacency list representation of the graph and performs BFS starting from node 0. The `visited` array helps keep track of visited nodes to avoid revisiting them. When a node is processed (i.e., added to the `result` vector), it is removed from the queue and its unvisited neighbors are added to the queue.

[FAIL] - This solution assumes that the graph is undirected, which may not be true in some competitive programming scenarios. In such cases, additional checks should be added to handle directed graphs appropriately. Additionally, the input/output is assumed to follow a specific format, which may vary from problem to problem. The time complexity of this BFS implementation is O(V + E), where V is the number of vertices and E is the number of edges in the graph.