from collections import defaultdict, deque
import pandas as pd
import math

class Multigrafo:
    def __init__(self):
        self.V = set()
        self.E = []     
        self.A = []      
        self.VR = set()
        self.ER = set()
        self.AR = set()
        self.adjacencia = defaultdict(list)
        self.demanda_vertices = {}

    def adicionar_vertice(self, v, demanda=0, requerido=False):
        self.V.add(v)
        self.demanda_vertices[v] = demanda
        if requerido:
            self.VR.add(v)

    def adicionar_aresta(self, u, v, custo=1, demanda=0, requerido=False):
        self.V.add(u)
        self.V.add(v)
        self.E.append((u, v, custo, demanda))
        self.adjacencia[u].append((v, custo))
        self.adjacencia[v].append((u, custo))
        if requerido:
            self.ER.add(frozenset((u, v)))

    def adicionar_arco(self, u, v, custo=1, demanda=0, requerido=False):
        self.V.add(u)
        self.V.add(v)
        self.A.append((u, v, custo, demanda))
        self.adjacencia[u].append((v, custo))
        if requerido:
            self.AR.add((u, v))


    def grau_dos_vertices(self):
        graus = defaultdict(int)
        for u in self.adjacencia:
            graus[u] += len(self.adjacencia[u])
            for v, _ in self.adjacencia[u]:
                graus[v] += 1
        return graus

    def componentes_conectados(self):
        visitado = set()
        componentes = 0

        def bfs(v):
            fila = deque([v])
            visitado.add(v)
            while fila:
                u = fila.popleft()
                for vizinho, _ in self.adjacencia[u]:
                    if vizinho not in visitado:
                        visitado.add(vizinho)
                        fila.append(vizinho)

        for v in self.V:
            if v not in visitado:
                componentes += 1
                bfs(v)

        return componentes

    def floyd_warshall(self):
        V = list(self.V)
        index = {v: i for i, v in enumerate(V)}
        n = len(V)
        dist = [[math.inf] * n for _ in range(n)]
        pred = [[None] * n for _ in range(n)]

        for i in range(n):
            dist[i][i] = 0

        for u in self.adjacencia:
            for v, custo in self.adjacencia[u]:
                i, j = index[u], index[v]
                dist[i][j] = min(dist[i][j], custo)
                pred[i][j] = u

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i][j] > dist[i][k] + dist[k][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]
                        pred[i][j] = pred[k][j]

        return dist, pred, index

    def estatisticas(self):
        graus = self.grau_dos_vertices()
        dist_matrix, _, _ = self.floyd_warshall()

        n = len(self.V)
        m = len(self.E) + len(self.A)

        total_caminhos = 0
        soma_caminhos = 0
        diametro = 0

        for i in range(n):
            for j in range(n):
                if i != j and dist_matrix[i][j] != math.inf:
                    soma_caminhos += dist_matrix[i][j]
                    total_caminhos += 1
                    diametro = max(diametro, dist_matrix[i][j])

        caminho_medio = soma_caminhos / total_caminhos if total_caminhos > 0 else None

        return {
            'Quantidade de vértices': len(self.V),
            'Quantidade de arestas': len(self.E),
            'Quantidade de arcos': len(self.A),
            'Quantidade de vértices requeridos': len(self.VR),
            'Quantidade de arestas requeridas': len(self.ER),
            'Quantidade de arcos requeridos': len(self.AR),
            'Densidade do grafo': m / (n * (n - 1)) if n > 1 else 0,
            'Componentes conectados': self.componentes_conectados(),
            'Grau mínimo dos vértices': min(graus.values()) if graus else 0,
            'Grau máximo dos vértices': max(graus.values()) if graus else 0,
            'Caminho médio': caminho_medio,
            'Diâmetro': diametro
        }

    def vertices_as_dataframe(self):
        data = [
            {
                "Vértice": v,
                "Demanda": self.demanda_vertices.get(v, 0),
                "Obrigatório": v in self.VR
            }
            for v in self.V
        ]
        return pd.DataFrame(data)
    
    def arestas_as_dataframe(self):
        data = [
            {
                "Origem": u,
                "Destino": v,
                "Custo": custo,
                "Demanda": demanda,
                "Obrigatória": frozenset((u, v)) in self.ER
            }
            for u, v, custo, demanda in self.E
        ]
        return pd.DataFrame(data)


    def estatisticas_as_dataframe(self):
        stats = self.estatisticas()
        return pd.DataFrame(stats.items(), columns=["Métrica", "Valor"])
    
    def carregar_de_arquivo(self, caminho_arquivo: str):
        with open(caminho_arquivo, "r") as f:
            linhas = f.readlines()

        secao = None

        for linha in linhas:
            linha = linha.strip()

            # Ignorar linhas vazias
            if not linha:
                continue

            # Detectar seções
            if linha.startswith("ReN."):
                secao = "VERTICES"
                continue
            elif linha.startswith("ReE."):
                secao = "ARESTAS_REQUERIDAS"
                continue
            elif linha.startswith("EDGE"):
                secao = "ARESTAS"
                continue
            elif linha.startswith("ReA."):
                secao = "ARCOS_REQUERIDOS"
                continue
            elif linha.startswith("ARC"):
                secao = "ARCOS"
                continue

            # Processar de acordo com a seção atual
            if secao == "VERTICES":
                partes = linha.split()
                if len(partes) >= 3:
                    nome = partes[0]
                    demanda = int(partes[1])
                    self.adicionar_vertice(nome, demanda=demanda, requerido=True)

            elif secao == "ARESTAS_REQUERIDAS":
                partes = linha.split()
                if len(partes) >= 6:
                    origem = partes[1]
                    destino = partes[2]
                    custo = int(partes[3])
                    demanda = int(partes[4])
                    self.adicionar_aresta(origem, destino, custo, demanda=demanda, requerido=True)

            elif secao == "ARESTAS":
                partes = linha.split()
                if len(partes) >= 3:
                    origem = partes[0]
                    destino = partes[1]
                    custo = int(partes[2])
                    self.adicionar_aresta(origem, destino, custo, requerido=False)

            elif secao == "ARCOS_REQUERIDOS":
                partes = linha.split()
                if len(partes) >= 6:
                    origem = partes[1]
                    destino = partes[2]
                    custo = int(partes[3])
                    demanda = int(partes[4])
                    self.adicionar_arco(origem, destino, custo, requerido=True, demanda=demanda)

            elif secao == "ARCOS":
                partes = linha.split()
                if len(partes) >= 3:
                    origem = partes[1]
                    destino = partes[2]
                    custo = int(partes[3])
                    self.adicionar_arco(origem, destino, custo, requerido=False)
