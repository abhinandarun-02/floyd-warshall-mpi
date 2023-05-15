import numpy as np
import Pyro4

INFINITY = 1000000

@Pyro4.expose
class MatrixOperations:
    def __init__(self, n):
        self.n = n
        self.localmat = np.zeros(n * n, dtype=int)
        self.rowk = np.zeros(n, dtype=int)

    def read_matrix(self):
        if Pyro4.socketutil.getIpAddress(hostname='localhost') == self.owner(0):
            tempmat = np.zeros((self.n, self.n), dtype=int)
            print("Enter the local matrix:")
            for i in range(self.n):
                for j in range(self.n):
                    tempmat[i, j] = int(input())
        self.localmat = tempmat.flatten()


    def print_matrix(self):
        tempmat = np.reshape(self.localmat, (self.n, self.n))
        for i in range(self.n):
            for j in range(self.n):
                if tempmat[i, j] == INFINITY:
                    print("i", end=" ")
                else:
                    print(tempmat[i, j], end=" ")
            print()

    def floyd(self, globalk, rowk):
        root = self.owner(globalk)
        if Pyro4.socketutil.getIpAddress(hostname='localhost') == root:
            self.copy_row(rowk, globalk)
        else:
            rowk[:] = Pyro4.Proxy("PYRO:matrix_ops@{}:9090".format(root)).copy_row(globalk)

        for locali in range(self.n):
            for globalj in range(self.n):
                temp = self.localmat[locali * self.n + globalk] + rowk[globalj]
                if temp < self.localmat[locali * self.n + globalj]:
                    self.localmat[locali * self.n + globalj] = temp

    def owner(self, k):
        peers = Pyro4.locateNS().list(prefix="matrix_ops.")
        for name, uri in peers.items():
            if k < int(name.split(".")[-1]):
                return uri

    def copy_row(self, rowk, k):
        localk = k % self.n
        for j in range(self.n):
            rowk[j] = self.localmat[localk * self.n + j]

    def run(self):
        with Pyro4.Daemon() as daemon:
            uri = daemon.register(self)
            ns = Pyro4.locateNS()

            # Get the list of all peers from the nameserver
            peers = ns.list(prefix="matrix_ops.")

            # Connect to other peers
            for name, peer_uri in peers.items():
                if name != "matrix_ops.{}".format(Pyro4.socketutil.getIpAddress(hostname='localhost')):
                    print(name)

                    peer = Pyro4.Proxy(peer_uri)
                    peer._pyroTimeout = 5  # Set timeout for peer connections
                    peer.connect_to_peers(ns.list(prefix="matrix_ops."))

            ns.register("matrix_ops.{}".format(Pyro4.socketutil.getIpAddress(hostname='localhost')), uri)
            print("MatrixOperations server started at {}".format(Pyro4.socketutil.getIpAddress(hostname='localhost')))
            
            self.read_matrix()  # Prompt for matrix input
            
            daemon.requestLoop()

    def connect_to_peers(self, peers):
        for name, uri in peers.items():
            if name != "matrix_ops.{}".format(Pyro4.socketutil.getIpAddress(hostname='localhost')):
                if uri not in self._pyroDirectNS.lookup("matrix_ops.{}".format(Pyro4.socketutil.getIpAddress(hostname='localhost'))):
                    self._pyroDirectNS.register("matrix_ops.{}".format(Pyro4.socketutil.getIpAddress(hostname='localhost')), uri)


if __name__ == "__main__":
    print("How many vertices:")
    n = int(input())

    matrix_ops = MatrixOperations(n)
    matrix_ops.run()