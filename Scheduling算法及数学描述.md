# Scheduling Algorithms and Models

## 1. Static Priority (SP)

### A. Algorithm

![1626506836219](img/1626506836219.png)

- **Assumption**: non-preemptive, maybe finite size of buffers
- **Principle**: When the server becomes free (or after sending a packet), the scheduler always selects the packets at the head of the highest priority non-empty queue to work on.

#### **Scheduling Loop:**

```c++
while true do
    for i in 1..N do
        if not queue[i].empty() then
            SEND( queue[i].dequeue() )
            break
        end if
    end for
end while
```

Find a bug of static priority in `ns.py`, and open an issue in the GitHub.

### B. Procedure

![img](https://pic3.zhimg.com/80/v2-cc1707b42ddc9c8bd716f173850bb292_1440w.jpg)



## 2. Weighted Fair Queueing (WFQ)

### A. Algorithm

Need to see the code again, after seeing the paper.



## 3. Deficit Round Robin (RBB)

### A. Algorithm

#### Scheduling Loop

```python
while true do
    for i in 1..N do
        if not queue[i].empty() then
            DC[i]:= DC[i] + Q[i]
            while( not queue[i].empty() and DC[i] ≥ queue[i].head().size() ) do
                DC[i] := DC[i] − queue[i].head().size()
                SEND( queue[i].head() )
                queue[i].dequeue()
            end while 
        end if
    end for
end while
```

**Q**: What is the meaning of `head_of_line` in the code?

**A**: See the paper first, then ask if necessary.

### B. Procedure

Different Realization:

![preview](https://pic1.zhimg.com/v2-7bc3b14dba6c55f2e4ba5ed274524688_r.jpg)

## 4. HQoS