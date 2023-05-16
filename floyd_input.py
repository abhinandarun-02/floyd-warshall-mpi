from mpi4py import MPI
import numpy as np

INFINITY = 1000000

def read_matrix(localmat, n, myrank, p, comm):
    if myrank == 0:
        tempmat = np.zeros((n, n), dtype=int)
        print("Enter the local matrix:")
        for i in range(n):
            for j in range(n):
                tempmat[i, j] = int(input())
    else:
        tempmat = None
    
    comm.Scatter(tempmat, localmat, root=0)
    if myrank == 0:
        tempmat = None

def print_matrix(localmat, n, myrank, p, comm):
    if myrank == 0:
        tempmat = np.zeros((n, n), dtype=int)
    else:
        tempmat = None
    
    comm.Gather(localmat, tempmat, root=0)

    if myrank == 0:
        for i in range(n):
            for j in range(n):
                if tempmat[i, j] == INFINITY:
                    print("i", end=" ")
                else:
                    print(tempmat[i, j], end=" ")
            print()
        tempmat = None

def floyd(localmat, n, myrank, p, comm):
    rowk = np.zeros(n, dtype=int)
    for globalk in range(n):
        root = owner(globalk, p, n)
        if myrank == root:
            copy_row(localmat, n, p, rowk, globalk)
        comm.Bcast(rowk, root=root)
        for locali in range(n // p):
            for globalj in range(n):
                temp = localmat[locali * n + globalk] + rowk[globalj]
                if temp < localmat[locali * n + globalj]:
                    localmat[locali * n + globalj] = temp

def owner(k, p, n):
    return k // (n // p)

def copy_row(localmat, n, p, rowk, k):
    localk = k % (n // p)
    for j in range(n):
        rowk[j] = localmat[localk * n + j]

if __name__ == "__main__":
    comm = MPI.COMM_WORLD
    p = comm.Get_size()
    myrank = comm.Get_rank()

    if myrank == 0:
        print("How many vertices:")
        n = int(input())


    n = comm.bcast(n, root=0)
    localmat = np.zeros(n * n // p, dtype=int)

    read_matrix(localmat, n, myrank, p, comm)

    if myrank == 0:
        print("We got:")
    print_matrix(localmat, n, myrank, p, comm)

    floyd(localmat, n, myrank, p, comm)

    print()

    floyd(localmat, n, myrank, p, comm)

    if myrank == 0:
        print("The solution is:")
    print_matrix(localmat, n, myrank, p, comm)

    MPI.Finalize()
