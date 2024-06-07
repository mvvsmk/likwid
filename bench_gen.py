#! /usr/bin/env python3
import json

def generate_stream_like_benchmark(flops, bytes):
    # Constants
    scalar_avx_reg = "ymm{0}"
    load_avx_instr = "vmovaps ymm{0}, [STR1 + GPR1*8{1}]"
    fma_avx_instr_with_load = "vfmadd213pd ymm{0}, {1}, [STR2 + GPR1*8{2}]"
    store_instr = "vmovntpd [STR0 + GPR1*8{0}], ymm{1}"
    load_avx_instr_count = 0
    fma_avx_instr_with_load_count = 0
    store_avx_instr_count = 0

    # # Calculations
    loads = 2
    stores = 1
    # caluclation for count of load, fma and store instructions
    fma_avx_instr_with_load_count = 2 * flops
    load_avx_instr_count = int(((bytes / (loads + stores)) * (loads)) / 2 - fma_avx_instr_with_load_count)  # loads devided by 2 as float also performs load
    store_avx_instr_count = int((bytes / (loads + stores)) * stores / 2)
    print(f"Floats: {flops}, Bytes: {bytes}")
    print(f"Load: {load_avx_instr_count}, FMA: {fma_avx_instr_with_load_count}, Store: {store_avx_instr_count}")
    # exit()

    # instr_loop = 3 * fma_avx_instr_count + load_avx_instr_count + store_avx_instr_count  # Update this according to the logic
    loop = 2 * fma_avx_instr_with_load_count + load_avx_instr_count + store_avx_instr_count  # Update this according to the logic
    instr_const = loop + 16
    instr_loop = loop + 3
    uops = loop + 2


    # Benchmark Header
    benchmark = f"""\
STREAMS 3
TYPE DOUBLE
FLOPS {flops}
BYTES {bytes}
DESC Modified benchmark with {flops} FLOPS and {bytes} BYTES
LOADS {loads}
STORES {stores}
INSTR_CONST {instr_const}
INSTR_LOOP {instr_loop}
UOPS {uops}
vmovaps {scalar_avx_reg}, [rip+SCALAR]
LOOP {loop}"""

    # Load Instructions
    for i in range(load_avx_instr_count):
        benchmark += f"\n{load_avx_instr.format(i + 1, f"+{i * 32}" if i != 0 else "")}"
    
    # FMA Instructions
    for i in range(fma_avx_instr_with_load_count):
        benchmark += f"\n{fma_avx_instr_with_load.format(i % 8 + 1, scalar_avx_reg.format(load_avx_instr_count + 1), f"+{i * 32}" if i != 0 else "")}"
    
    # Store Instructions
    for i in range(store_avx_instr_count):
        benchmark += f"\n{store_instr.format(f"+{i * 32}" if i != 0 else "", i % 8 + 1)}"
    print(f"OI is {flops/bytes}")
    return benchmark

def generate_pure_float_and_load(flops=180, bytes=1) :

# one mem instruction is 2 bytes
# one fma instruction is 2 flops

    load_fma_init = 16
    load_avx_inside_loop = 0
    chosen_reg = 0

    total_fma_ops = 180
    total_loads = 1
    total_stores = 0


    #benchmark altering
    if bytes > 1 and bytes < 16:
        total_loads = bytes
        total_stores = 0
        total_fma_ops = flops * 2
    elif bytes >= 16 and bytes < 32:
        total_loads = 16
        total_stores = bytes - 16
        total_fma_ops = flops * 2
    elif bytes >= 32:
        total_loads = 16
        total_stores = 16
        total_fma_ops = total_fma_ops - (bytes -32)

    loop = total_fma_ops + total_loads + total_stores
    instr_const = loop + 16
    instr_loop = loop + 3
    uops = loop + 2

    streams = 3

    load_fma_int_instr = "vmovapd ymm{0}, [rip+SCALAR]"
    fma_instr = "vfmadd213pd ymm{0}, ymm{1}, ymm{2}"

    load_avx_int_instr = "vmovaps ymm{0}, [rip+SCALAR]"
    load_avx_instr = "vmovaps ymm{0}, [STR1 + GPR1*8{1}]"
    store_instr = "vmovntpd [STR0 + GPR1 * 8{0}], ymm{1}"

    total_init = 16

    loop_init ="LOOP {loop}"




    benchmark = f"""\
STREAMS {streams}
TYPE DOUBLE
FLOPS {flops}
BYTES {bytes}
DESC Modified benchmark with {flops} FLOPS and {bytes} BYTES
LOADS {total_loads}
STORES {total_stores}
INSTR_CONST {instr_const}
INSTR_LOOP {instr_loop}
UOPS {uops}"""
    #initialization
    for i in range(load_fma_init):
        benchmark += f"\n{load_fma_int_instr.format(i % 16)}"

    #LOOP INIT
    benchmark += f"\n{loop_init.format(loop=loop)}"

    # Load Instructions
    for i in range(total_loads):
        if i == 0:
            benchmark += f"\n{load_avx_instr.format(chosen_reg, f"+{i * 32}" if i != 0 else "")}"
        else:
            benchmark += f"\n{load_avx_instr.format(i + 1, f"+{i * 32}" if i != 0 else "")}"

    # FMA Instructions
    for i in range(total_fma_ops + 1) :
        if i % 16 == chosen_reg:
            continue
        benchmark += f"\n{fma_instr.format(i % 16, i % 16,chosen_reg)}"

    # Store Instructions
    for i in range(total_stores):
        benchmark += f"\n{store_instr.format(f"+{i * 32}" if i != 0 else "", i % 8 + 1)}"

    print(f"OI is {flops/bytes}")
    return benchmark


def break_down_into_2_to_1(mem_ops) :
    if mem_ops == 1:
        return 1, 0

    store = int(mem_ops // 3)
    load = int(mem_ops - store)
    return load, store

def generate_pure_float_and_load_v2(flops=180, bytes=2) :

# assumption #1
# one mem instruction is 2 bytes
# one fma instruction is 2 flops

    total_fma_ops_req = int(flops / 2)
    total_mem_ops_req = int(bytes / 2)

    total_load_ops_req, total_store_ops_req = break_down_into_2_to_1(total_mem_ops_req)
    chosen_reg = 0

    loop = total_fma_ops_req + total_load_ops_req + total_store_ops_req
    loop = loop if loop > 16 else 16 # assumption 2 as loop gives segfault if the number is very low 
    instr_const = loop + 16
    instr_loop = loop + 3
    uops = loop + 2
    streams = 3

    if total_store_ops_req > 0:
        streams = 2
    else:
        streams = 1

    load_fma_int_instr = "vmovapd ymm{0}, [rip+SCALAR]"
    fma_instr = "vfmadd213pd ymm{0}, ymm{1}, ymm{2}"

    load_avx_int_instr = "vmovaps ymm{0}, [rip+SCALAR]"
    load_avx_instr = "vmovaps ymm{0}, [STR0 + GPR1*8{1}]"
    store_instr = "vmovntpd [STR1 + GPR1 * 8{0}], ymm{1}"
    loop_init ="LOOP {loop}"

    # total_init = 1 if total_fma_ops_req > 0 else 0
    total_init = total_fma_ops_req - total_load_ops_req + 1
    if total_init < 0:
        total_init = 1

    total_init = int(total_init)

    benchmark = f"""\
STREAMS {streams}
TYPE DOUBLE
FLOPS {flops}
BYTES {bytes}
DESC Modified benchmark with {flops} FLOPS and {bytes} BYTES
LOADS {total_load_ops_req}
STORES {total_store_ops_req}
INSTR_CONST {instr_const}
INSTR_LOOP {instr_loop}
UOPS {uops}"""

    print(f"Total FMA Ops: {total_fma_ops_req}, Total Mem Ops: {total_mem_ops_req}")
    print(f"Total Load Ops: {total_load_ops_req}, Total Store Ops: {total_store_ops_req}")
    print(f"total_init: {total_init}")
    #initialization
    for i in range(total_init if total_init < 16 else 16):
        benchmark += f"\n{load_fma_int_instr.format(i % 16)}"
    #LOOP INIT
    benchmark += f"\n{loop_init.format(loop=loop)}"

    # Load Instructions
    for i in range(total_load_ops_req):
        # if i == 0:
        #     benchmark += f"\n{load_avx_instr.format(chosen_reg, f"+{i * 32}" if i != 0 else "")}"
        # else:
            benchmark += f"\n{load_avx_instr.format(i , f"+{i * 32}" if i != 0 else "")}"

    print(range(total_fma_ops_req + 1))
    flop_reg_numbers = []
    while len(flop_reg_numbers) < total_fma_ops_req:
        for i in range(1,16):
            flop_reg_numbers.append(i)
            if len(flop_reg_numbers) == total_fma_ops_req:
                break

    # FMA Instructions
    for i in flop_reg_numbers :
        # print(i)
        if i % 16 == chosen_reg:
            continue
        # test = f"{fma_instr.format(i % 16, i % 16,chosen_reg)}"
        # print(f"i: {i} : {test}")
        benchmark += f"\n{fma_instr.format(i % 16, i % 16,chosen_reg)}"

    # Store Instructions
    for i in range(total_store_ops_req):
        benchmark += f"\n{store_instr.format(f"+{i * 32}" if i != 0 else "", i % 8 + 1)}"

    print(f"Total FMA Ops: {total_fma_ops_req}, Total Mem Ops: {total_mem_ops_req}")
    print(f"Total Load Ops: {total_load_ops_req}, Total Store Ops: {total_store_ops_req}")
    print(f"OI is {flops/bytes}")
    return benchmark

#-----------------


if __name__ == "__main__":
    oi = [0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256]
    oi_list =[[2, 8], [4, 8], [8, 8], [16, 8], [32, 8], [64, 8], [128, 8], [256, 8], [512, 8], [1024, 8], [2048, 8]]
    print("Generating benchmarks for OI 0.25 to 256")
    print(f"oi is {oi}")
    for i in oi_list:
        print(f"oi is {i[0] / i[1]}")

    output_files = []
    count = 0
    for i in oi_list:
        print(generate_pure_float_and_load_v2(flops=i[0], bytes=i[1]))
        #write the output to a file
        output_file = f"OI_TEST{count}.ptt"
        output_files.append(output_file)
        with open(output_file, "w") as f:
            f.write(generate_pure_float_and_load_v2(flops=i[0], bytes=i[1]))
        count += 1

    # export the output files list to a json file
    with open("output_files.json", "w") as f:
        json.dump(output_files, f)
    
    #read from the json file and print the output files
    with open("output_files.json", "r") as f:
        output_files = json.load(f)
        print(output_files)
    
    # # flops = 2
    # # bytes = 6
    # # print(generate_pure_float_and_load(flops, bytes))
    # print(generate_pure_float_and_load_v2(flops=flops, bytes=bytes))
    # print(f"OI is {flops/bytes}")
    """
    Hey nilesh bhaiya, I have finished up with benchmark generator script, 
    the OI I have tested are [0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256] 
    with the following configuration[[2, 8], [4, 8], [8, 8], [16, 8], [32, 8], [64, 8], [128, 8], [256, 8], [512, 8], [1024, 8], [2048, 8]]
    this is flops, bytes used for each OI
    The scripts were giving a segfault initially but now I have rectified it.
    There are 2 assumptions I have made and they are mentioned in the script.
    """