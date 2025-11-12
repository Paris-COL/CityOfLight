#Structure of the shared-memory segment.

G_HDR, ACT_BYTES  = 48, 20
C_HDR             = 16

HP_BYTES          = 84             # 19 × 4 B  (after the 4-B state int)
LOG_BYTES         = 256
FUNC_BYTES        = 4
ARGS_BYTES        = 2048

HP_OFF   = G_HDR + ACT_BYTES                 # 0x0028
LOG_OFF  = HP_OFF + HP_BYTES                 # 0x0074
FUNC_OFF = LOG_OFF + LOG_BYTES               # 0x0174
ARGS_OFF = FUNC_OFF + FUNC_BYTES             # 0x0178
CAM_OFF  = ARGS_OFF + ARGS_BYTES             # 0x0188

ACT_OFF  = G_HDR
FMT      = "<iiiii"          # idx, fwd, turn, vert, grav

MAX_RESOLUTION = 2048
BPP            = 4
BLOCK_STRIDE   = C_HDR + MAX_RESOLUTION * MAX_RESOLUTION * BPP

order      = ["RGB", "Depth", "Normals","Semantic"]

MAX_CAMERAS = len(order)
