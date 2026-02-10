"""
Danh sach co phieu thanh phan cua cac chi so.
Cap nhat: 02/02/2026 (ky thang 1/2026: VPL vao, BCM ra)
Nguon: HOSE, Vietstock

Luu y: Danh muc duoc ra soat 2 lan/nam (thang 1 va thang 7).
"""

# VN30: 30 co phieu von hoa lon nhat HOSE
VN30 = [
    "ACB", "BID", "BVH", "CTG", "DGC",
    "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW",
    "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIC",
    "VJC", "VNM", "VPB", "VPL", "VRE",
]

# VN100 & VNMIDCAP: se duoc tu dong xac dinh tu price_board.csv
# VN100 = top 100 co phieu HOSE theo gia tri giao dich
# VNMIDCAP = co phieu trong VN100 nhung khong thuoc VN30
