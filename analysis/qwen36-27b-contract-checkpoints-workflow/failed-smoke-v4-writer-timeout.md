# Failed smoke v4: implementation writer timeout

Tool isolation worked: the isolation audit had zero violations and read-only roles exposed only read/bash.
The workflow stopped after four agents because `thin slice implementation` hit its 1,200,000 ms timeout while actively debugging two failing integration tests. It produced a nonempty patch and was not stalled.

The writer timeout was increased to 1,500,000 ms. The maximum six-stage child critical path is now 4,800,000 ms (80 minutes), within the 90-minute parent budget.
