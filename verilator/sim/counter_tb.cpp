// Testbench for counter module using Verilator
#include <stdio.h>
#include <stdlib.h>
#include <verilated.h>
#include "Vcounter.h"

// Current simulation time
vluint64_t main_time = 0;

// Called by $time in Verilog
double sc_time_stamp() {
    return main_time;
}

int main(int argc, char** argv) {
    // Initialize Verilator
    Verilated::commandArgs(argc, argv);
    
    // Create instance of counter module
    Vcounter* counter = new Vcounter;
    
    // Reset sequence
    counter->rst_n = 0;
    counter->enable = 0;
    counter->clk = 0;
    
    printf("Starting counter simulation...\n");
    printf("Time\tReset\tEnable\tCount\n");
    printf("====\t=====\t======\t=====\n");
    
    // Run simulation for several clock cycles
    for (int i = 0; i < 100; i++) {
        // Toggle clock
        counter->clk = !counter->clk;
        
        // Release reset after a few cycles
        if (i > 10) {
            counter->rst_n = 1;
        }
        
        // Enable counting after reset
        if (i > 20) {
            counter->enable = 1;
        }
        
        // Evaluate model
        counter->eval();
        
        // Print on positive clock edge
        if (counter->clk && i % 2 == 1) {
            printf("%3d\t%d\t%d\t%3d\n", 
                   i/2, counter->rst_n, counter->enable, counter->count);
        }
        
        main_time++;
    }
    
    // Final model cleanup
    counter->final();
    
    // Destroy model
    delete counter;
    
    printf("\nSimulation completed successfully!\n");
    
    return 0;
}
