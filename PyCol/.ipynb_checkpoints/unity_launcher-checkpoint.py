import os, subprocess, signal, ctypes, time, mmap, struct
import numpy as np
from .static_flags import *
def _pdeathsig_preexec(sig=signal.SIGTERM):
    """
    Child hook (runs in the child just before exec):
    If the parent dies, the kernel sends `sig` to this process to stop it.
    """
    def _fn():
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        PR_SET_PDEATHSIG = 1
        # If parent already gone between fork and this call, bail out.
        if os.getppid() == 1:
            os._exit(1)
        if libc.prctl(PR_SET_PDEATHSIG, sig) != 0:
            # On error, still proceed; Unity will just not auto-exit on parent death.
            pass
    return _fn

def launch_unity_instance(UNITY_EXE,LOG_DIR, batch_mode=False, *extra_args):
    """
    Launch Unity; it will receive SIGTERM automatically if this Python process dies.
    Returns a subprocess.Popen handle.
    """


    args = [
        UNITY_EXE,
        "-screen-fullscreen", "0",
        "-screen-width", "100",
        "-screen-height", "100",
        "-logFile", os.path.join(LOG_DIR, "logs.log"),
    ]

    # ─── Conditional batch/headless mode ───
    if batch_mode:
        args += [
            "-batchmode",   # disables the Unity Editor UI, makes it non-interactive
        ]
    args += list(extra_args)

    return subprocess.Popen(args, preexec_fn=_pdeathsig_preexec(signal.SIGTERM))

def close(proc):
    """Closes Unity player."""
    if proc.poll() is None:
        proc.terminate()          # SIGTERM
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()           # SIGKILL fallback
            
def populate(config):
    HP = {
    "speedFactor":     config['speed_factor'],
    "spawnPeds":       config['spawn_pedestrians'],
    "spawnCars":       config['spawn_cars'],
    "moveSpeed":       config['move_speed'],
    "turnSpeed":       config['turn_speed'],
    "verticalSpeed":   config['vertical_speed'],
    "momentum":        config['momentum'],
    "fixedDeltaTime":  config['fixedDeltaTime'],
    "nActions":        config['number_of_steps'],
    "rgb":             config['rgb_camera'],
    "depth":           config['depth_camera'],
    "normals":         config['normals_camera'],
    "semantic":        config['semantic_camera'],
    "imageWidth":      config['IMG_SIZE'],          # NEW – width  (px)
    "imageHeight":     config['IMG_SIZE'],          # NEW – height (px)
    "vFOV":            config['vertical_fov'],         # NEW – vertical field-of-view (deg)
    "startX":          config['start_x'],
    "startY":          config['start_y'],
    "startZ":          config['start_z'],
    "launch_streaming":config['launch_streaming'],
    "render":          config['render']
    }
    return(HP)
    
    
def shm_size_bytes():
    CAM_OFF = G_HDR + ACT_BYTES + HP_BYTES + LOG_BYTES + FUNC_BYTES + ARGS_BYTES
    bytes_per_cam = C_HDR + MAX_RESOLUTION * MAX_RESOLUTION * BPP
    return CAM_OFF + bytes_per_cam * MAX_CAMERAS
    
def prepare_shm(MAP_NAME = "paris3d_ipc", timeout: float = 30.0):
    """
    Prepares the shared memory segment for python.
    Waits (up to 'timeout' seconds) for Unity to create /dev/shm/<MAP_NAME>.
    """

    if os.name == 'posix':
        shm_path = f"/dev/shm/{MAP_NAME}"

        # Wait until Unity creates the shared memory file
        start = time.time()
        while not os.path.exists(shm_path):
            if time.time() - start > timeout:
                raise FileNotFoundError(
                    f"Shared memory file {shm_path} not found after {timeout}s. "
                    "Unity may not have started yet."
                )
            time.sleep(0.1)

        fd = os.open(shm_path, os.O_RDWR)
        shm = mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE)
        os.close(fd)

    else:
        size = shm_size_bytes()
        shm = mmap.mmap(-1, size, tagname=MAP_NAME, access=mmap.ACCESS_WRITE)

    return shm

    
def check_unity_readiness(shm, timeout: float = 3.0) -> bool:
    """
    Wait until Unity signals readiness (HP_OFF == 0).
    
    Parameters
    ----------
    timeout : float
        Number of seconds to wait. If <= 0, check only once.
    
    Returns
    -------
    bool
        True if Unity is ready within timeout, False otherwise.
    """
    deadline = time.time() + timeout
    while True:
        if struct.unpack_from("<I", shm, HP_OFF)[0] == 0:
            return True
        if timeout > 0 and time.time() >= deadline:
            return False
        time.sleep(0.01)  # small sleep to avoid busy spin
    
def parametrize(shm, HP, timeout: float = 30) -> float:
    """
    Send hyper-parameters and wait for Unity to acknowledge (HP_OFF -> 2).

    Parameters
    ----------
    shm : mmap.mmap
    HP  : dict
    timeout : float | None
        Max seconds to wait for ACK. None => wait indefinitely.

    Returns
    -------
    float
        Elapsed seconds until Unity acknowledgement.

    Raises
    ------
    TimeoutError
        If timeout is set and expires before ACK.
    """
    hp_fmt  = "<fII5f9I4f"
    hp_blob = struct.pack(
        hp_fmt,
        HP["speedFactor"],
        HP["spawnPeds"],  HP["spawnCars"],
        HP["moveSpeed"],  HP["turnSpeed"],  HP["verticalSpeed"],
        HP["momentum"],   HP["fixedDeltaTime"],
        HP["nActions"],
        HP["rgb"],        HP["depth"],      HP["normals"],
        HP["semantic"],   HP["launch_streaming"], HP["render"], HP["imageWidth"], HP["imageHeight"],
        HP["vFOV"],
        HP["startX"],     HP["startY"],     HP["startZ"],
    )

    # Send
    shm[HP_OFF + 4 : HP_OFF + 4 + HP_BYTES] = hp_blob
    shm[HP_OFF : HP_OFF + 4] = struct.pack("<I", 1)  # hpState = 1 (pending)
    print("▶ hyper-parameters sent – waiting for Unity …")

    t0 = time.monotonic()
    while True:
        if struct.unpack_from("<I", shm, HP_OFF)[0] == 2:  # ACK
            elapsed = time.monotonic() - t0
            print("✔ Unity acknowledged hyper-parameters – simulation running")
            return True
        else:
            shm[HP_OFF + 4 : HP_OFF + 4 + HP_BYTES] = hp_blob
            shm[HP_OFF : HP_OFF + 4] = struct.pack("<I", 1)  # hpState = 1 (pending)
            time.sleep(0.1)

        if timeout is not None and (time.monotonic() - t0) >= timeout:
            return(False)



def prepare_frames(shm, HP):
    frames = {}
    frame_idx, n_cam, px, py, pz, rx, ry, rz = struct.unpack_from("<IIffffff", shm, 0)
    print(f"{n_cam} camera(s) – player at ({px:.2f}, {py:.2f}, {pz:.2f})")
    
    active     = [HP["rgb"], HP["depth"], HP["normals"], HP["semantic"]]
    label_iter = (lbl for lbl, flag in zip(order, active) if flag)
    
    # ────────────────────────────────
    # 6.  Walk through the camera blocks
    # ────────────────────────────────
    
    off = CAM_OFF
    for cam_idx in range(n_cam):
        cid, w, h, chan = struct.unpack_from("<IIII", shm, off)
        pix_off   = off + C_HDR
        pix_bytes = w * h * chan
    
        label = next(label_iter, f"cam{cam_idx}")
        print(f"{label}: {w}×{h}  chan={chan}  off=0x{pix_off:X}")
    
        BufType = ctypes.c_uint8 * pix_bytes
        buf     = BufType.from_buffer(shm, pix_off)
        frame   = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, chan)
        frames[label] = frame
    
        off += BLOCK_STRIDE
    return(frames,active)