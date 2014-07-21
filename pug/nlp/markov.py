# -*- coding: utf-8 -*-
# by Lizhong Zheng <lizhong@MIT.EDU>

import numpy as np
# import os
import random
import math

def GaussianDataFile():
    
    f=open('GaussianData','w')
    
    f.write('# Gaussian vector of length k, each comes from X_i= sqrt(1-r^2) X_{i-1} + r W_i \n')
    f.write('# First line: n=number of samples, k=dimension per sample, Nt= first Nt values training \n')
    
    n = 1000
    k = 8
    r = 0.4
    s = np.sqrt(1-r*r)

    f.write(str(n) +', '+ str(k)+', ' + str(0) +'\n')
    
    for i in range(n):
        x=np.random.normal()
        f.write("%2.4f" %x)
        
        for j in range(k-1):
            x=s*x+ r*np.random.normal()
            f.write(', '+ "%2.4f" %x)
            
        f.write('\n')
    f.close()
    
def MarkovDataFile():
    
    f=open('MarkovData','w')
    f.write('# two Markov chains both with uniform steady state distributions\n')
    
# two transition matrices, each marked by integers, with LCM = 10

#  Take the convention W1[i] is the conditional distribution P_Y|X=i    
    
    W1= [[0.4,0.3,0.2,0.1],[0.1,0.4,0.3,0.2],[0.2,0.1,0.4,0.3],[0.3,0.2,0.1,0.4]]
    W2= [[0.2,0.3,0.3,0.2],[0.2,0.2,0.3,0.3],[0.3,0.2,0.2,0.3],[0.3,0.3,0.2,0.2]]
    
    f.write('# First line: n=number of samples, k=dimension per sample, Nt= first Nt values training \n')
    
    n=1000
    k=200
    Nt=1
    f.write(str(n) +', '+ str(k)+', ' + str(Nt) +'\n')
    
    for i in range(n):
        U=random.randint(0,1)
        if U==0:
            WW= W1
        else:
            WW= W2
            
    # write the lable   
        
        f.write(" %4d" %U)    
        
    # first sample
        x=random.randint(0,3)
        f.write(", %4d" %x)
        for j in range(k-1):
        
        # generate next sample a given distribution 
            x=np.random.choice(4, p=WW[x])
            f.write(", %4d" %x)
        
        f.write('\n')
    
    f.close()

        
    
def ReadDataFile(filename):
    
    f= open(filename,'r')
    
    str=f.readline()
    
 # lines starting with '#' are descriptions   
    while (str[0]=='#'):
        str=f.readline()
  
 #  first useful line gives the size of the array. 
       
    templist=str.split(", ")
    
    n= int(templist[0])
    k= int(templist[1])
    str=templist[2]    
    Nt= int(str[: str.find('\n')])
    
    Data=[]
    for i in range(n):
        str=f.readline()
        templist=str.split(", ")
        Data.append([float(x) for x in templist])
        
    return n,k,Nt, Data
        
        
def SimpleSVD(filename):

    n,k,Nt, Data = ReadDataFile(filename)

   # Simple PCA
    
    Data= np.array (Data)

# Empirical covariance matrix
    Kx= np.transpose(Data).dot(Data)/n

# Eigenvalues and Eigenvectors    
    Lambda, U= np.linalg.eig(Kx)

    print(Lambda)      
    
def RandomScore(Nt, Data):

# metric[i][j] is a map that takes (X_{n-1}, X_n)=(i,j) to a random value   
    metric=[range(4)]*4
    for i in range(4):
        for j in range(4):
            metric[i][j]=np.random.random()

    score = range(len(Data))        
    for i in range(len(Data)):
        score[i]=0
        
        for j in range(len(Data[0])-Nt-1):
            score[i]+= metric[int(Data[i][Nt+j])][int(Data[i][Nt+j+1])]
        
        score[i]=score[i]/(len(Data[0])-Nt)

    return score
    
def CheckClasses(score, Data):
    index0=[i for i in range(len(Data)) if Data[i][0]==0]
    index1=[i for i in range(len(Data)) if Data[i][0]==1]
    score0 =[score[i] for i in index0]
    score1 =[score[i] for i in index1]
    
    avg0=np.sum(score0)/len(score0)
    avg1=np.sum(score1)/len(score1)

    var0= np.sum([(score0[i]-avg0)*(score0[i]-avg0) for i in range(len(score0))])/len(score0)    
    var1= np.sum([(score1[i]-avg1)*(score1[i]-avg1) for i in range(len(score1))])/len(score1)  
    print ("Number of samples in class 0 =%d\n" %len(score0))
    print("Avg score for class 0 = %4.4f \n" %avg0)
    print("Variance for class 0 = %4.4f \n" %var0)
    print ("Number of samples in class 1 =%d\n" %len(score1))
    print("Avg score for class 1 = %4.4f \n" %avg1)
    print("Variance for class 1 = %4.4f \n" %var1)

def SVDScore(Nt, Data):
       
    W1= [[0.4,0.3,0.2,0.1],[0.1,0.4,0.3,0.2],[0.2,0.1,0.4,0.3],[0.3,0.2,0.1,0.4]]
    W2= [[0.2,0.3,0.3,0.2],[0.2,0.2,0.3,0.3],[0.3,0.2,0.2,0.3],[0.3,0.3,0.2,0.2]]

# V is the nominal transition matrix between X_{n-1} and X_n, can be learned 
# from empirical distributions
    
    V=W1
    dim=len(W1)
    
    for i in range(dim):
        for j in range(dim):
            V[i][j]=(W1[i][j]+W2[i][j])/2
            
# W is the noisy observation matrix, which is assumed to be the quternary 
#  symmetric channel          
    
    W= [[0.4,0.2,0.2,0.2],[0.2,0.4,0.2,0.2],[0.2,0.2,0.4,0.2],[0.2,0.2,0.2,0.4]]

    U,L,Vt= np.linalg.svd(W)
# the 4 vectors are Vt[0] = [1/2,1/2,1/2,1/2]
#                   Vt[1] = [0, 0, 1, -1] /sqrt(2)
#                   Vt[2] = [0, 2, -1, -1] /sqrt(6)
#                   Vt[3] = [3, -1, -1, -1]/sqrt(12)     
    
    Px12 = np.ones((dim, dim))       # stores the joint distribution of two samples
    dPx12 = np.ones((dim, dim))      # stores the difference between joint distribution and indpendent
    
    for i in range(dim):
        for j in range(dim):
            Px12[i][j] = W[i][j] /4.0
            dPx12[i][j] = Px12[i][j] - 1/16.0
    
    Py12 = np.ones((dim, dim))    # stores the joint distribution of two noisy samples

    for i in range(dim):
        
        for j in range(dim):
            
            sum=0
            for ii in range(dim):
                for jj in range(dim):
                    sum+= Px12[ii][jj]*W[ii][i]*W[jj][j]
            
            Py12[i][j] = sum
   
# Generate the two symbol B matrix
    
    B= np.ones((dim*dim, dim*dim))
    
    for y1 in range(dim):
        for y2 in range(dim):
            for x1 in range(dim):
                for x2 in range(dim):
                    B[y1*dim+y2][x1*dim+x2]= W[x1][y1]*W[x2][y2]* np.sqrt(Px12[x1][x2]/Py12[y1][y2])
            
    
    Ub, Lb, Vb = np.linalg.svd(B)
    
#Lb[0]=1
    
    metric = Vb[1].reshape((dim, dim))
    
    score = range(len(Data))        
    for i in range(len(Data)):
        
        score[i]=0

        for j in range(len(Data[0])-Nt-1):
            
            score[i]+= metric[int(Data[i][Nt+j])][int(Data[i][Nt+j+1])]
        score[i]=score[i]/(len(Data[0])-Nt)

    return(score)   
    
def OptimalScore(Nt, Data, dim=4):

# The best score function
    W1= [[0.4,0.3,0.2,0.1],[0.1,0.4,0.3,0.2],[0.2,0.1,0.4,0.3],[0.3,0.2,0.1,0.4]]
    W2= [[0.2,0.3,0.3,0.2],[0.2,0.2,0.3,0.3],[0.3,0.2,0.2,0.3],[0.3,0.3,0.2,0.2]]
    
    metric = np.ones((dim, dim)) 
    
    for i in range(dim):
        for j in range(dim):
            metric[i][j]= math.log(W2[i][j]/W1[i][j])

    
    score = range(len(Data))        
    for i in range(len(Data)):
        
        score[i]=0

        for j in range(len(Data[0])-Nt-1):
            
            score[i]+= metric[int(Data[i][Nt+j])][int(Data[i][Nt+j+1])]
        score[i]=score[i]/(len(Data[0])-Nt)
   
   
    return(score)

def Top3Score(Nt, Data, dim=4):
    
    NTop = 6  # the number of top scores to be calculated
    
    W1= [[0.4,0.3,0.2,0.1],[0.1,0.4,0.3,0.2],[0.2,0.1,0.4,0.3],[0.3,0.2,0.1,0.4]]
    W2= [[0.2,0.3,0.3,0.2],[0.2,0.2,0.3,0.3],[0.3,0.2,0.2,0.3],[0.3,0.3,0.2,0.2]]

# V is the nominal transition matrix between X_{n-1} and X_n, can be learned 
# from empirical distributions
    
    V=W1
    dim=len(W1)
    
    for i in range(dim):
        for j in range(dim):
            V[i][j]=(W1[i][j]+W2[i][j])/2
            
# W is the noisy observation matrix, which is assumed to be the quternary 
#  symmetric channel          
    
    W= [[0.4,0.2,0.2,0.2],[0.2,0.4,0.2,0.2],[0.2,0.2,0.4,0.2],[0.2,0.2,0.2,0.4]]

    U,L,Vt= np.linalg.svd(W)
# the 4 vectors are Vt[0] = [1/2,1/2,1/2,1/2]
#                   Vt[1] = [0, 0, 1, -1] /sqrt(2)
#                   Vt[2] = [0, 2, -1, -1] /sqrt(6)
#                   Vt[3] = [3, -1, -1, -1]/sqrt(12)     
    
    Px12 = np.ones((dim, dim))       # stores the joint distribution of two samples
    dPx12 = np.ones((dim, dim))      # stores the difference between joint distribution and indpendent
    
    for i in range(dim):
        for j in range(dim):
            Px12[i][j] = W[i][j] /4.0
            dPx12[i][j] = Px12[i][j] - 1/16.0
    
    Py12 = np.ones((dim, dim))    # stores the joint distribution of two noisy samples

    for i in range(dim):
        
        for j in range(dim):
            
            sum=0
            for ii in range(dim):
                for jj in range(dim):
                    sum+= Px12[ii][jj]*W[ii][i]*W[jj][j]
            
            Py12[i][j] = sum
   
# Generate the two symbol B matrix
    
    B= np.ones((dim*dim, dim*dim))
    
    for y1 in range(dim):
        for y2 in range(dim):
            for x1 in range(dim):
                for x2 in range(dim):
                    B[y1*dim+y2][x1*dim+x2]= W[x1][y1]*W[x2][y2]* np.sqrt(Px12[x1][x2]/Py12[y1][y2])
            
    
    Ub, Lb, Vb = np.linalg.svd(B)
    
#Lb[0]=1
    
    scorearray=np.ones((NTop, len(Data)))
    score = range(len(Data))  
    
    for nTop in range(NTop):
        metric = Vb[1+nTop].reshape((dim, dim))
    
        for i in range(len(Data)):
        
            scorearray[nTop][i]=0

            for j in range(len(Data[0])-Nt-1):
            
                scorearray[nTop][i]+= metric[int(Data[i][Nt+j])][int(Data[i][Nt+j+1])]
            
            scorearray[nTop][i]=scorearray[nTop][i]/(len(Data[0])-Nt)

    S=np.matrix(scorearray)*np.matrix(scorearray).transpose() #covariance matrix
    Ls, Us = np.linalg.eig(S)  # Us[:,i] is the eigenvector for Ls[i]
    
    for i in range(len(Data)):
        score[i]= np.sum([Us[j,0]*scorearray[j,i] for j in range(NTop)])
        # take inner product to the first eigenvector 

    return(score)


def test():
      
    dim = 4
    # write 'GaussianData' to store a Gaussian Markov data file
    #    GaussianDataFile()
    #    SimpleSVD('GaussianData')   

    # generage mixed Markov data, uncomment to generate a new one
    # comment out for repeating on the same data
    MarkovDataFile()

    # read data in any data file    
    [n,k, Nt, Data] = ReadDataFile('MarkovData')

    # randomly pick a score function based on two adjacent samples    
    #    score =RandomScore(Nt, Data)
    #    CheckClasses(score, Data)

 
    # Compute SVD w.r.t. a noisy observation and score with it
    score = SVDScore(Nt, Data)
    print(" SVD Scores:\n ")
    CheckClasses(score, Data)

    # Compute the best metric from log likelihood, and score with it
    score = OptimalScore(Nt, Data, dim=dim)    
    print(" Optimal Scores: \n")
    CheckClasses(score, Data)
    
    # Compute the top 3 scores from SVD and then do a 3-D PCA
    score = Top3Score(Nt, Data)
    print(" Top 3 Score PCA :\n")
    CheckClasses(score, Data)
   

    Alpha = np.ones((dim, dim))   # Alpha is the coefficients of dPx12 w.r.t. Vt[i]\otimes Vt[j]
    
    for i in range(dim):

        for j in range(dim):

            sum=0
            
            for ii in range(dim):
                for jj in range(dim):
#                   sum+= dPx12[ii][jj] * Vt[i][ii]*Vt[j][jj]
                   sum+= i                    
                    
            Alpha[i][j] = sum

# Alpha[0][0] is useless, and from dPx12 to Alpha is a rotation, the following
# checks the normal is unchanged. 
#    sum1=0
#    sum2=0
#    for i in range(4):
#        for j in range(4):
#            sum1+=Alpha[i][j]**2
#            sum2+= dPx12[i][j]**2


if __name__ == "__main__":
    test()