#!/usr/bin/python
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QDialog,QGroupBox, QPushButton, QLineEdit, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

import random
import math

class Window(QWidget):
    xgrid=[]
    data=[]
    fit=[]
    rng1=random.SystemRandom()
    rng2=random.SystemRandom()

    def __init__(self):
        super().__init__()
               
        #---Control buttons---
        self.btnread = QPushButton('Read Data', self)
        self.btnreset = QPushButton('Reset Fitting', self)
        self.btnfit1 = QPushButton('Fit 1x', self)
        self.btnfit100 = QPushButton('Fit 100x', self)

        self.energy=QLabel("Energy: -, steps: 0",self)

        layout=QHBoxLayout(self)
        layout.addWidget(self.btnread)
        layout.addWidget(self.btnreset)
        layout.addWidget(self.btnfit1)
        layout.addWidget(self.btnfit100)
        layout.addWidget(self.energy)
        #layout.addStretch()
        self.control_buttons=QGroupBox()
        self.control_buttons.setLayout(layout)
        #------

        #---Parameter boxes
        self.titleBeta = QLabel("Beta",self)
        self.Beta = QLineEdit("100",self)

        self.titleA = QLabel("A",self)
        self.initA = QLineEdit("1",self)
        self.stepA = QLineEdit("0.1",self)

        self.titleTau = QLabel("Tau",self)
        self.initTau = QLineEdit("130",self)
        self.stepTau = QLineEdit("10",self)

        self.titleT = QLabel("T",self)
        self.initT = QLineEdit("200",self)
        self.stepT = QLineEdit("10",self)

        layout=QGridLayout(self)
        layout.addWidget(self.titleBeta,0,0)
        layout.addWidget(self.Beta,0,1)
        layout.addWidget(self.titleA,1,0)
        layout.addWidget(self.initA,1,1)
        layout.addWidget(self.stepA,1,2)
        layout.addWidget(self.titleTau,2,0)
        layout.addWidget(self.initTau,2,1)
        layout.addWidget(self.stepTau,2,2)
        layout.addWidget(self.titleT,3,0)
        layout.addWidget(self.initT,3,1)
        layout.addWidget(self.stepT,3,2)
        layout.setColumnStretch(2,0)
        self.param_boxes=QGroupBox()
        self.param_boxes.setLayout(layout)
        #------

        #---Main plot---
        self.main_plot = plt.figure()
        self.main_canvas = FigureCanvas(self.main_plot)
        #------ 

        #---Final layout---
        layout=QVBoxLayout(self)
        layout.addWidget(self.main_canvas)
        layout.addWidget(self.control_buttons)
        layout.addWidget(self.param_boxes)
        layout.addStretch()
        self.setLayout(layout)

        self.setWindowTitle('Monte-Carlo fitting')
        self.show()
        #------

        #---Control button actions---
        self.btnread.clicked.connect(self._read_data)
        self.btnreset.clicked.connect(self._reset)
        self.btnfit1.clicked.connect(self._fit1)
        self.btnfit100.clicked.connect(self._fit100)
        #------

    #reads data series from a textfile
    #required format: xvalue whitespace yvalue newline (for each point)
    def _read_data(self):
        #resetting the data and x values arrays and the iteration counter
        self.cnt=0
        self.data=[]
        self.xgrid=[]
        self.energy.setText("Energy: -, steps: 0")

        from PyQt5.QtWidgets import QFileDialog
        fname=QFileDialog.getOpenFileName()[0]
        try:
            fin=open(fname,"r")
        except FileNotFoundError as e:
            print("File not found.")
            return

        try:
            for line in fin:
                self.data.append(float(line.split()[1]))
                self.xgrid.append(float(line.split()[0]))
            self._plot_data()
        except Exception as e:
            print(e.__class__.__name__+": "+str(e))
            print("Invalid file.")
            self.data=[]
            self.xgrid=[]
        fin.close()

    #draws the data points
    def _plot_data(self):
        self.main_plot.clear()
        ax = self.main_plot.add_subplot(111)
        ax.plot(self.data, '+')
        self.main_canvas.draw()

    #Gets the values from the LineEdits
    def _getparams(self):
        #reading the values        
        self.beta=float(self.Beta.text())
        self.A=float(self.initA.text())
        self.dA=float(self.stepA.text())
        self.tau=float(self.initTau.text())
        self.dtau=float(self.stepTau.text())
        self.T=float(self.initT.text())
        self.dT=float(self.stepT.text())

        #initializing the array of fitted values and the energy
        self.E=0
        for i in range(len(self.xgrid)):
            x=self.xgrid[i]
            self.fit.append(self.A*math.exp(-x/self.tau)*math.sin(2*math.pi*x/self.T))
            self.E+=abs(self.data[i]-self.fit[-1])
        

    #Writes the modified parameters back to the LineEdits
    def _setparams(self):        
        self.initA.setText(str(self.A))
        self.initTau.setText(str(self.tau))
        self.initT.setText(str(self.T))

    #Executes one fitting step
    def _fit1(self):
        self.fit=[]
        try:
            self._getparams()
        except Exception as e:
            print(e.__class__.__name__+": "+str(e))
            print("Invalid parameter.")
            return
        self._fit()
        self._plot_fit()
        self._setparams()

    #Executes 100 fitting steps      
    def _fit100(self):
        self.fit=[]
        try:
            self._getparams()
        except Exception as e:
            print(e.__class__.__name__+": "+str(e))
            print("Invalid parameter.")
            return
        [self._fit() for i in range(100)]
        self._plot_fit()
        self._setparams()

    def _func(self, A, tau, T):
        fit=[0]
        E=0
        for i in range(len(self.xgrid)):
            x=self.xgrid[i]
            fit.append(A*math.exp(-x/tau)*math.sin(2*math.pi*x/T))
            E+=abs(self.data[i]-fit[i])
        return fit, E

    #performs a fitting step
    def _fit(self):
        self.cnt+=1

        A=self.A+self.dA*(1-2*self.rng1.random())
        fit, E = self._func(A, self.tau, self.T)
        if((E<self.E) or (self.rng2.random()<math.exp(-self.beta*abs(E-self.E)))):
            self.E=E
            self.fit=fit
            self.A=A

        tau=self.tau+self.dtau*(1-2*self.rng1.random())
        fit, E = self._func(self.A, tau, self.T)
        if((E<self.E) or (self.rng2.random()<math.exp(-self.beta*abs(E-self.E)))):
            self.E=E
            self.fit=fit
            self.tau=tau

        T=self.T+self.dT*(1-2*self.rng1.random())
        fit, E = self._func(self.A, self.tau, T)
        if((E<self.E) or (self.rng2.random()<math.exp(-self.beta*abs(E-self.E)))):
            self.E=E
            self.fit=fit
            self.T=T

    #draws the data points and the fitted curve and writes the energy
    def _plot_fit(self):
        self.main_plot.clear()
        ax = self.main_plot.add_subplot(111)
        ax.plot(self.data, '+')
        ax.plot(self.fit, '-')
        self.main_canvas.draw()

        self.energy.setText("Energy: {:.5E}, steps: {}".format(self.E, self.cnt))

    #resets the iteration counter and deletes the fitted curve
    def _reset(self):
        self.cnt=0
        self._plot_data()
        self.energy=QLabel("Energy: -, steps: 0",self)

#MAIN
if __name__ == '__main__':    
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec_()) 
