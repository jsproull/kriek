
class pidpy(object):
    ek_1 = 0.0  # e[k-1] = SP[k-1] - PV[k-1] = Tset_hlt[k-1] - Thlt[k-1]
    ek_2 = 0.0  # e[k-2] = SP[k-2] - PV[k-2] = Tset_hlt[k-2] - Thlt[k-2]
    xk_1 = 0.0  # PV[k-1] = Thlt[k-1]
    xk_2 = 0.0  # PV[k-2] = Thlt[k-1]
    yk_1 = 0.0  # y[k-1] = Gamma[k-1]
    yk_2 = 0.0  # y[k-2] = Gamma[k-1]
    lpf_1 = 0.0 # lpf[k-1] = LPF output[k-1]
    lpf_2 = 0.0 # lpf[k-2] = LPF output[k-2]
    
    yk = 0.0 # output
    
    GMA_HLIM = 100.0
    GMA_LLIM = 0.0
    
    def __init__(self, pid):
        self.pid = pid
    	
        #self.kc = kc
        #self.ti = ti
        #self.td = td
        #self.ts = ts
        
        self.k_lpf = 0.0
        self.k0 = 0.0
        self.k1 = 0.0
        self.k2 = 0.0
        self.k3 = 0.0
        self.lpf1 = 0.0
        self.lpf2 = 0.0
        self.ts_ticks = 0
        self.pid_model = 3
        self.pp = 0.0
        self.pi = 0.0
        self.pd = 0.0
        if (self.pid.i_param == 0.0):
            self.k0 = 0.0
        else:
            self.k0 = self.pid.k_param * self.pid.cycle_time / self.pid.i_param
        self.k1 = self.pid.k_param * self.pid.d_param/ self.pid.cycle_time
        self.lpf1 = (2.0 * self.k_lpf - self.pid.cycle_time) / (2.0 * self.k_lpf + self.pid.cycle_time)
        self.lpf2 = self.pid.cycle_time / (2.0 * self.k_lpf + self.pid.cycle_time) 
        
    def calcPID_reg3(self, xk, tset, enable):
        ek = 0.0
        lpf = 0.0
        ek = tset - xk # calculate e[k] = SP[k] - PV[k]

	    #ek = abs(ek)

        #--------------------------------------
        # Calculate Lowpass Filter for D-term
        #--------------------------------------
        lpf = self.lpf1 * pidpy.lpf_1 + self.lpf2 * (ek + pidpy.ek_1);
        
        if (enable):
            #-----------------------------------------------------------
            # Calculate PID controller:
            # y[k] = y[k-1] + kc*(e[k] - e[k-1] +
            # Ts*e[k]/Ti +
            # Td/Ts*(lpf[k] - 2*lpf[k-1] + lpf[k-2]))
            #-----------------------------------------------------------
            self.pp = self.pid.k_param * (ek - pidpy.ek_1) # y[k] = y[k-1] + Kc*(PV[k-1] - PV[k])
            self.pi = self.k0 * ek  # + Kc*Ts/Ti * e[k]
            self.pd = self.k1 * (lpf - 2.0 * pidpy.lpf_1 + pidpy.lpf_2)
            pidpy.yk += self.pp + self.pi + self.pd
        else:
            pidpy.yk = 0.0
            self.pp = 0.0
            self.pi = 0.0
            self.pd = 0.0
        
        pidpy.ek_1 = ek # e[k-1] = e[k]
        pidpy.lpf_2 = pidpy.lpf_1 # update stores for LPF
        pidpy.lpf_1 = lpf
            
        # limit y[k] to GMA_HLIM and GMA_LLIM
        if (pidpy.yk > pidpy.GMA_HLIM):
            pidpy.yk = pidpy.GMA_HLIM
        if (pidpy.yk < pidpy.GMA_LLIM):
            pidpy.yk = pidpy.GMA_LLIM

        #print "Current temp: " + str(xk) + " Target temp: " + str(tset) + " Diff : " + str(ek)
        #print "self.pid.k_param " + str(self.pid.k_param) + " self.pid.i_param " + str(self.pid.i_param) + " self.pid.d_param " + str(self.pid.d_param) + " self.pid.cycle_time " + str(self.pid.cycle_time)
        #print "pidpy.xk_1 " + str(pidpy.xk_1) + " pidpy.xk_2 " + str(pidpy.xk_2)
         
        return pidpy.yk
                          
    def calcPID_reg4(self, xk, tset, enable):
        ek = 0.0
        ek = tset - xk # calculate e[k] = SP[k] - PV[k]
        
        #print "Current temp: " + str(xk) + " Target temp: " + str(tset) + " Diff : " + str(ek)
        #print "self.pid.k_param " + str(self.pid.k_param) + " self.pid.i_param " + str(self.pid.i_param) + " self.pid.d_param " + str(self.pid.d_param) + " self.pid.cycle_time " + str(self.pid.cycle_time)
        #print "pidpy.xk_1 " + str(pidpy.xk_1) + " pidpy.xk_2 " + str(pidpy.xk_2)
        if (enable):
            #-----------------------------------------------------------
            # Calculate PID controller:
            # y[k] = y[k-1] + kc*(PV[k-1] - PV[k] +
            # Ts*e[k]/Ti +
            # Td/Ts*(2*PV[k-1] - PV[k] - PV[k-2]))
            #-----------------------------------------------------------
            self.pp = self.pid.k_param * (pidpy.xk_1 - xk) # y[k] = y[k-1] + Kc*(PV[k-1] - PV[k])
            self.pi = self.k0 * ek  # + Kc*Ts/Ti * e[k]
            self.pd = self.k1 * (2.0 * pidpy.xk_1 - xk - pidpy.xk_2)
            pidpy.yk += self.pp + self.pi + self.pd
        else:
            pidpy.yk = 0.0
            self.pp = 0.0
            self.pi = 0.0
            self.pd = 0.0
        
        #print "self.pp " + str(self.pp) + " self.pi " + str(self.pi) + " self.pd " + str(self.pd) 
        pidpy.xk_2 = pidpy.xk_1  # PV[k-2] = PV[k-1]
        pidpy.xk_1 = xk    # PV[k-1] = PV[k]
        #print "PID Value: " + str(pidpy.yk) + " xk1: " + str(xk) + " xk2: " + str(pidpy.xk_2)
        
        # limit y[k] to GMA_HLIM and GMA_LLIM
        if (pidpy.yk > pidpy.GMA_HLIM):
            pidpy.yk = pidpy.GMA_HLIM
        if (pidpy.yk < pidpy.GMA_LLIM):
            pidpy.yk = pidpy.GMA_LLIM
        
        
        return pidpy.yk
        

if __name__=="__main__":

    sampleTime = 2
    pid = PID(sampleTime,0,0,0)
    temp = 80
    setpoint = 100
    enable = True
    #print pid.calcPID_reg4(temp, setpoint, enable)
    
