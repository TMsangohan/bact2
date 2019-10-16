#!/usr/bin/env python
# coding: utf-8

# In[10]:


from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, PVPositionerPC, Signal
import bluesky.plans as bp
from bluesky import RunEngine
import functools


# In[23]:


class PowerConverter(PVPositionerPC):
    setpoint = Cpt(EpicsSignal,   ':set')
    readback = Cpt(EpicsSignalRO, ':rdbk')
    
    # If used as PVPositioner .... 
    # but study first how much the offset has to be
    done    =  Cpt(EpicsSignalRO, ':stat8')
    
class SextupoleCollection(Device):
    s3pdr = PowerConverter('S3PDR', settle_time = .1)
    s3ptr = PowerConverter('S3PTR', settle_time = .1)

    s4pdr = PowerConverter('S4PDR', settle_time = .1)
    s4ptr = PowerConverter('S4PTR', settle_time = .1)
    


# In[33]:


sp = SextupoleCollection(name = 'sc')

powerconverters = [
    sp.s3pdr #, sp.s3ptr, 
     #sp.s4pdr, sp.s4ptr
                  ]


# In[34]:


sp.s3pdr.setpoint.value


# In[35]:


try:
    RE
except NameError:
    RE = RunEngine({})


# In[36]:


for pc in powerconverters:
    if not pc.connected:
        pc.wait_for_connection()
        

RE(bp.count(powerconverters))


# In[11]:


# No I refrain from hacking on a user machine
# s3pdr = PowerConverter('S3PDR', settle_time = .1)
# s4ptr = PowerConverter('S3PTR')

# s4pdf = PowerConverter('S4PDR')
# s4ptr = PowerConverter('S4PTR')


# excute a relative list scan
# but first find out if a relative scan uses the setpoint or 
# the read back as value ....


# alternative : find values first 
# and make a list scan


#ref = [sp.s3pd]
cmd = functools.partial(bp.list_scan, )


# In[6]:


#RE(cmd())


# In[ ]:




