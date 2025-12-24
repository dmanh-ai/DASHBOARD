// DỮ LIỆU ĐẦY ĐỦ CHO VNINDEX - 100% TỪ FILE GỐC
// Template có thể tái sử dụng cho các báo cáo khác

const FULL_DATA = {
    vnindex: {
        title: "VNINDEX - PHÂN TÍCH ĐẦY ĐỦ 100%",
        sections: [
            {
                icon: "📊",
                title: "THÔNG TIN CHUNG",
                content: `
                    <div class="info-box">
                        <h4>Giá & Thay Đổi</h4>
                        <p><strong>Giá hiện tại:</strong> <span class="highlight">1,772 điểm</span></p>
                        <p><strong>Thay đổi 1D:</strong> <span class="highlight">+1.21%</span></p>
                        <p><strong>Thay đổi 5D:</strong> <span class="highlight">+5.54%</span></p>
                        <p><strong>Thay đổi 20D:</strong> <span class="highlight">+6.73%</span></p>
                        <p><strong>Khối lượng:</strong> 859.5 tỷ</p>
                    </div>
                    <div class="info-box">
                        <h4>Tổng Quan</h4>
                        <p>VNINDEX đang trong <span class="highlight">xu hướng tăng mạnh</span> trong ngắn hạn, tăng vừa trong trung hạn và tăng trong dài hạn.</p>
                        <p>Ngắn hạn: <span class="warning">Quá mua cực độ</span> (RSI5=94.69)</p>
                        <p>Trung hạn: Tăng vừa (Mom20=6.73, ADX20=15.06)</p>
                        <p>Dài hạn: Tăng mạnh (Mom200=33.22 dương mạnh)</p>
                    </div>
                `
            },
            {
                icon: "📈",
                title: "XU HƯỚNG GIÁ",
                content: `
                    <div class="info-box">
                        <h4>Ngắn Hạn (1-5 phiên)</h4>
                        <p><strong>Kết luận:</strong> <span class="highlight">Tăng mạnh</span></p>
                        <p>Giá (1,772) <span class="highlight">> MA5 (1,716)</span> và MA10 (1,697)</p>
                        <p>Thay đổi 5D = <span class="highlight">+5.54%</span>, Mom5 = 5.54 dương</p>
                        <p>ADX5 = <span class="highlight">43.83 > 25</span>, xác nhận xu hướng tăng mạnh</p>
                        <p><span class="danger">⚠️ RSI5 = 94.69</span> - Thị trường ở trạng thái quá mua cực độ!</p>
                    </div>
                    <div class="info-box">
                        <h4>Trung Hạn (20-50 phiên)</h4>
                        <p><strong>Kết luận:</strong> <span class="highlight">Tăng vừa</span></p>
                        <p>Giá <span class="highlight">> MA20 (1,708)</span> và MA50 (1,679)</p>
                        <p>Thay đổi 20D = <span class="highlight">+6.73%</span>, Mom20 = 6.73 dương</p>
                        <p>ADX20 = 15.06 (<25) - Xu hướng có nhưng chưa cực kỳ mạnh</p>
                    </div>
                    <div class="info-box">
                        <h4>Dài Hạn (>50 phiên)</h4>
                        <p><strong>Kết luận:</strong> <span class="highlight">Tăng</span></p>
                        <p>Giá <span class="highlight">> MA100 (1,667)</span> và MA200 (1,502)</p>
                        <p>Mom100 = 18.52, Mom200 = <span class="highlight">33.22 dương mạnh</span></p>
                        <p>ADX100 và ADX200 đều dưới 25</p>
                    </div>
                    <div class="info-box">
                        <h4>Kiểm Tra Divergence/Alignment</h4>
                        <p><strong>Không có tín hiệu bearish divergence</strong> rõ ràng</p>
                        <p>RSI5 (94.69), RSI20 (66.52), RSI50 (50.62) đều đồng hành với đà tăng của giá</p>
                        <p>ADX5 (43.83) cao và ADX20 (15.06), ADX50 (10.76) thấp hơn</p>
                        <p>→ Xu hướng tăng tập trung mạnh ở ngắn hạn</p>
                        <p><strong>Ý nghĩa:</strong> Xu hướng tổng thể nghiêng về tăng, đặc biệt mạnh trong ngắn hạn</p>
                        <p><span class="warning">Cảnh báo:</span> RSI5 quá mua → rủi ro điều chỉnh kỹ thuật trong vài phiên tới</p>
                    </div>
                `
            },
            {
                icon: "📊",
                title: "XU HƯỚNG KHỐI LƯỢNG",
                content: `
                    <div class="info-box">
                        <h4>Kết Luận</h4>
                        <p>Khối lượng hiện tại <span class="highlight">cao hơn trung bình ngắn và trung hạn</span>, nhưng thấp hơn trung bình dài hạn.</p>
                        <p>Xu hướng khối lượng trong 10 phiên gần đây <span class="warning">biến động mạnh</span>.</p>
                    </div>
                    <div class="info-box">
                        <h4>Dẫn Chứng Chi Tiết</h4>
                        <p><strong>Khối lượng phiên hiện tại (T-0):</strong> 859,542,980</p>
                        <p><strong>So với trung bình:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.8;">
                            <li>Cao hơn VMA10 (758,174,547) ✓</li>
                            <li>Cao hơn VMA20 (761,529,309) ✓</li>
                            <li>Cao hơn VMA50 (849,270,678) ✓</li>
                            <li><span class="danger">Thấp hơn</span> VMA100 (1,112,513,055) ✗</li>
                        </ul>
                    </div>
                    <div class="info-box">
                        <h4>Diễn Biến 10 Phiên</h4>
                        <p>Khối lượng dao động lớn:</p>
                        <p>• Thấp nhất: 592 triệu (T-8)</p>
                        <p>• Cao nhất: 980 triệu (T-1)</p>
                        <p>→ Không có xu hướng tăng/giảm ổn định</p>
                    </div>
                    <div class="info-box">
                        <h4>Ý Nghĩa & Hành Động</h4>
                        <p>Khối lượng giao dịch gần đây ở mức khá so với trung bình ngắn hạn</p>
                        <p>Nhưng chưa thể hiện sự bùng nổ bền vững nếu so với trung bình dài hạn</p>
                        <p><strong>Cần theo dõi:</strong> Khối lượng có duy trì được trên các mức VMA hay không?</p>
                    </div>
                `
            },
            {
                icon: "💹",
                title: "KẾT HỢP XU HƯỚNG GIÁ & KHỐI LƯỢNG",
                content: `
                    <div class="info-box">
                        <h4>Kết Luận</h4>
                        <p>Giá tăng mạnh ngắn hạn nhưng <span class="warning">thiếu sự đồng thuận hoàn toàn</span> từ khối lượng.</p>
                        <p>Trung hạn có sự đồng thuận tốt hơn.</p>
                    </div>
                    <div class="info-box">
                        <h4>Ngắn Hạn</h4>
                        <p>Giá tăng <span class="highlight">5.54%</span> trong 5 phiên</p>
                        <p>Nhưng khối lượng phiên T-0 (859 triệu) <span class="danger"><</span> đỉnh khối lượng T-1 (980 triệu)</p>
                        <p>→ Sức mua có thể không còn dồn dập như phiên trước</p>
                    </div>
                    <div class="info-box">
                        <h4>Trung Hạn</h4>
                        <p>Giá tăng <span class="highlight">6.73%</span> trong 20 phiên</p>
                        <p>Khối lượng phiên hiện tại vẫn cao hơn VMA20 (761 triệu)</p>
                        <p>→ Thể hiện sự đồng thuận tương đối tốt</p>
                    </div>
                    <div class="info-box">
                        <h4>Dài Hạn</h4>
                        <p>Giá tăng mạnh so với MA200</p>
                        <p>Nhưng khối lượng lại thấp hơn VMA100</p>
                        <p>→ <span class="warning">Sự đồng thuận yếu</span></p>
                    </div>
                    <div class="info-box">
                        <h4>Momentum Cascade</h4>
                        <p>Mom20 (<span class="highlight">6.73</span>) > Mom5 (5.54)</p>
                        <p>→ Động lượng tăng trung hạn hiện tại mạnh hơn động lượng tăng ngắn hạn</p>
                        <p>→ Tín hiệu tích cực cho xu hướng trung hạn</p>
                        <p><span class="warning">Nhưng:</span> Đà tăng ngắn hạn đang cho thấy dấu hiệu mệt mỏi</p>
                    </div>
                    <div class="info-box">
                        <h4>Ý Nghĩa</h4>
                        <p>Xu hướng tăng trung hạn có độ tin cậy cao hơn nhờ động lượng và khối lượng hỗ trợ</p>
                        <p>Đà tăng ngắn hạn đang cho thấy dấu hiệu mệt mỏi, cần cảnh giác với điều chỉnh</p>
                    </div>
                `
            },
            {
                icon: "⚖️",
                title: "CUNG - CẦU",
                content: `
                    <div class="info-box">
                        <h4>Kết Luận</h4>
                        <p>Áp lực mua <span class="highlight">đang chiếm ưu thế</span>, đẩy giá vượt lên trên vùng giá trị trung tâm (Value Area).</p>
                        <p>Tuy nhiên, giá đang tiến vào vùng có thể xuất hiện cung (bán) mạnh.</p>
                    </div>
                    <div class="info-box">
                        <h4>Vùng Cầu (Hỗ trợ/Mua)</h4>
                        <p><strong>POC:</strong> 1,654 - Vùng tập trung nhiều giao dịch nhất → Sẽ đóng vai trò hỗ trợ mạnh nếu giá điều chỉnh</p>
                        <p><strong>Value Area:</strong> 1,635 - 1,769</p>
                        <p>Giá hiện tại nằm ngay ở <span class="highlight">rìa trên</span> của Value Area</p>
                    </div>
                    <div class="info-box">
                        <h4>Vùng Cung (Kháng cự/Bán)</h4>
                        <p><strong>Ngay lập tức:</strong> 1,778 (đỉnh phiên T-0) đến 1,780 (Band trên Bollinger 20)</p>
                        <p>→ Vùng kháng cự tức thì</p>
                        <p><strong>Tiếp theo:</strong> Band trên Bollinger 5 ở 1,804</p>
                    </div>
                    <div class="info-box">
                        <h4>Ưu Thế</h4>
                        <p>Giá hiện tại nằm trên <span class="highlight">tất cả các mức VWAP</span>:</p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>VWAP5 = 1,721 ✓</li>
                            <li>VWAP20 = 1,709 ✓</li>
                            <li>VWAP50 = 1,680 ✓</li>
                        </ul>
                        <p>→ Bên mua đang nắm lợi thế trên mọi khung thời gian</p>
                        <p>CMF20 (<span class="highlight">0.16</span>) và CMF200 (<span class="highlight">0.17</span>) dương mạnh</p>
                        <p>→ Xác nhận dòng tiền đang chảy vào thị trường</p>
                    </div>
                    <div class="info-box">
                        <h4>Ý Nghĩa & Hành Động</h4>
                        <p><span class="highlight">Bên mua đang kiểm soát.</span></p>
                        <p>Nhà đầu tư hiện tại có thể tiếp tục nắm giữ.</p>
                        <p>Nhưng nhà đầu tư mới muốn mua nên thận trọng ở vùng giá hiện tại:</p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Giá gần kháng cự (1,778-1,780)</li>
                            <li>RSI quá mua</li>
                        </ul>
                        <p><strong>Điểm vào lý tưởng hơn:</strong> Vùng hỗ trợ POC 1,654 hoặc MA20</p>
                    </div>
                `
            },
            {
                icon: "🎯",
                title: "MỨC GIÁ QUAN TRỌNG",
                content: `
                    <div class="info-box warning">
                        <h4>Kháng Cự (Bên bán chiếm ưu thế)</h4>
                        <p><strong>1,778 - 1,780:</strong> Đây là vùng kháng cự mạnh</p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Kết hợp giữa đỉnh trong ngày (H=1,778)</li>
                            <li>Band trên Bollinger 20 (1,780)</li>
                        </ul>
                        <p><strong>Độ tin cậy: CAO</strong></p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>1,804:</strong> Band trên Bollinger 5</p>
                        <p>→ Kháng cự ngắn hạn tiếp theo nếu giá vượt qua 1,780</p>
                    </div>
                    <div class="info-box">
                        <h4>Hỗ Trợ (Bên mua chiếm ưu thế)</h4>
                        <p><strong>1,708 (MA20):</strong> Hỗ trợ động trung hạn quan trọng</p>
                        <p><strong>Độ tin cậy: Trung bình - CAO</strong></p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>1,697 (MA10):</strong> Hỗ trợ động ngắn hạn</p>
                        <p><strong>Độ tin cậy: Trung bình</strong></p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>1,654 (POC):</strong> Hỗ trợ mạnh nhất dựa trên cấu trúc khối lượng lịch sử</p>
                        <p>Đây là vùng tích lũy/phân phối chính</p>
                        <p><strong>Độ tin cậy: CAO</strong></p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>1,636 - 1,629:</strong> Vùng hỗ trợ mạnh khác</p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Band dưới Bollinger 20 (1,636)</li>
                            <li>Đáy của 20 phiên gần nhất (L=1,629)</li>
                        </ul>
                    </div>
                    <div class="info-box">
                        <h4>Ý Nghĩa & Hành Động</h4>
                        <p><strong>Kịch bản tăng:</strong> Cần vượt qua 1,780 để mở đường lên 1,804</p>
                        <p><strong>Kịch bản điều chỉnh:</strong> Mức thoái lui quan trọng để quan sát phản ứng mua là 1,708 và 1,654</p>
                        <p><span class="danger">Điều kiện khiến kết luận sai:</span> Giá phá vỡ và đóng cửa dứt khoát dưới 1,629 (hỗ trợ mạnh) hoặc trên 1,804 (kháng cự mạnh)</p>
                    </div>
                `
            },
            {
                icon: "📉",
                title: "BIẾN ĐỘNG GIÁ",
                content: `
                    <div class="info-box">
                        <h4>Kết Luận</h4>
                        <p>Biến động giá ở mức <span class="warning">cao trong ngắn hạn</span> và trung bình trong trung/dài hạn.</p>
                        <p><span class="highlight">KHÔNG</span> có tín hiệu "squeeze" (thắt chặt biến động).</p>
                    </div>
                    <div class="info-box">
                        <h4>ATR (Average True Range)</h4>
                        <p>ATR5 (<span class="highlight">26.04</span>) cao hơn ATR200 (25.58)</p>
                        <p>→ Biến động ngắn hạn đang cao hơn biến động dài hạn</p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p>ATR10 = <span class="highlight">34.63</span> - Cao nhất</p>
                        <p>→ Phản ánh một số phiên biến động mạnh trong vòng 10 phiên qua</p>
                    </div>
                    <div class="info-box">
                        <h4>Bollinger Band Width</h4>
                        <p>Width của BB20 = <span class="highlight">8.4%</span></p>
                        <p>→ Biến động trung bình</p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p>Width của BB5 = <span class="warning">10.3%</span></p>
                        <p>→ Biến động ngắn hạn cao hơn một chút</p>
                    </div>
                    <div class="info-box">
                        <h4>TTM Squeeze</h4>
                        <p><strong>Dữ liệu:</strong> "KHÔNG (BB20 rộng hơn KC20)"</p>
                        <p>Cụ thể:</p>
                        <ul style="margin-left: 20px; line-height: 1.8;">
                            <li>Dải Bollinger 20: <span class="highlight">1,636 - 1,780</span></li>
                            <li>Dải Keltner 20: 1,644 - 1,760</li>
                        </ul>
                        <p>→ BB20 rộng hơn KC20</p>
                        <p><strong>Ý nghĩa:</strong> Biến động KHÔNG bị thắt chặt mà đang ở trạng thái mở rộng hoặc bình thường</p>
                        <p>→ <span class="highlight">Không tạo ra áp lực</span> cho một đợt bùng nổ giá lớn sắp tới</p>
                    </div>
                    <div class="info-box">
                        <h4>Ý Nghĩa & Hành Động</h4>
                        <p>Thị trường đang có biến động tương đối</p>
                        <p>Phù hợp với xu hướng tăng có điều chỉnh</p>
                        <p><span class="highlight">Không có tín hiệu báo trước</span> một đợt biến động mạnh (breakout/breakdown)</p>
                        <p>từ trạng thái tích lũy chặt</p>
                        <p><span class="warning">Điều kiện sai:</span> Nếu BB20 thu hẹp đáng kể và nằm hoàn toàn trong KC20, tín hiệu "squeeze" sẽ xuất hiện</p>
                    </div>
                `
            },
            {
                icon: "🕯️",
                title: "MÔ HÌNH GIÁ - MÔ HÌNH NẾN",
                content: `
                    <div class="info-box">
                        <h4>Kết Luận</h4>
                        <p><strong>Không có mô hình giá kinh điển</strong> (Double Top, Triangle...) rõ ràng trong 20 phiên.</p>
                        <p>Chuỗi nến gần nhất thể hiện đà tăng mạnh nhưng đang chậm lại.</p>
                    </div>
                    <div class="info-box">
                        <h4>Mô Hình Giá</h4>
                        <p>Quan sát dữ liệu 20 phiên:</p>
                        <p>Giá tạo thành một xu hướng tăng với:</p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li><span class="highlight">Higher Highs</span> (Đỉnh cao dần)</li>
                            <li><span class="highlight">Higher Lows</span> (Đáy cao dần)</li>
                        </ul>
                        <p>→ Không hình thành các mẫu hình cụ thể</p>
                    </div>
                    <div class="info-box">
                        <h4>Mô Hình Nến</h4>
                        <p><strong>Phiên T-2 và T-1:</strong> Hai nến tăng liên tiếp với thân nến dài</p>
                        <p>Đặc biệt phiên T-1:</p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Close = 1,751, Open = 1,717</li>
                            <li>→ Là một nến tăng mạnh, khẳng định sức mua</li>
                        </ul>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>Phiên T-0 (hiện tại):</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Nến có thân nhỏ (Close=1,772, Open=1,765)</li>
                            <li>Bóng trên ngắn, nằm gần đỉnh của phiên</li>
                            <li>→ <span class="warning">Dấu hiệu của sự do dự</span> sau hai phiên tăng mạnh</li>
                            <li>→ Áp lực mua không còn áp đảo</li>
                        </ul>
                    </div>
                    <div class="info-box">
                        <h4>Hidden Divergence (Stochastic)</h4>
                        <p><strong>Không tìm thấy</strong> tín hiệu hidden divergence đáng tin cậy</p>
                        <p>Cả Stoch_K5 (94.66) và Stoch_K20 (95.95) đều ở vùng quá mua rất cao</p>
                        <p>Đang di chuyển đồng hướng với giá tăng</p>
                        <p>→ <span class="highlight">Không có sự phân kỳ</span> giữa đà oscillator và đà giá</p>
                    </div>
                    <div class="info-box">
                        <h4>Ý Nghĩa & Hành Động</h4>
                        <p>Sự xuất hiện của nến thân nhỏ sau đợt tăng mạnh là <span class="warning">cảnh báo ngắn hạn</span></p>
                        <p>về khả năng tạm dừng hoặc điều chỉnh nhẹ.</p>
                        <p><strong>Cần theo dõi:</strong> Nến của phiên tiếp theo để xác nhận</p>
                        <p><span class="highlight">Điều kiện sai:</span> Nếu phiên tiếp theo lại hình thành một nến tăng thân dài, phá lên trên 1,778</p>
                        <p>→ Mô hình nến sẽ lại trở nên tích cực, bác bỏ dấu hiệu do dự</p>
                    </div>
                `
            },
            {
                icon: "👥",
                title: "MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG",
                content: `
                    <div class="info-box danger">
                        <h4>Kết Luận: Bearish</h4>
                        <p>Trạng thái breadth hiện tại <span class="danger">nghiêng về bearish</span> với áp lực bán rộng rãi,</p>
                        <p>nếu có một số yếu tố giảm nhẹ mức độ tiêu cực.</p>
                    </div>
                    <div class="info-box">
                        <h4>Dẫn Chứng & Phân Tích</h4>
                        <p><strong>Số mã giảm (218)</strong> gần gấp đôi số mã tăng (113)</p>
                        <p>→ Phản ánh áp lực bán lan rộng</p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>TRIN = 1.03 (>1)</strong></p>
                        <p>→ Hỗ trợ nhận định bearish</p>
                        <p>→ Volume trên nhóm mã giảm có phần áp đảo</p>
                        <p><span class="warning">Nhưng mức 1.03 không quá cực đoan</span></p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>Volume Ratio = 0.50x</strong></p>
                        <p>→ củng cố tín hiệu bearish</p>
                        <p>→ Gợi ý khối lượng giao dịch trên các mã giảm lớn hơn đáng kể so với mã tăng</p>
                    </div>
                    <div class="info-box">
                        <h4>Điểm Nhẹ Hàng</h4>
                        <p><strong>52W Highs (12)</strong> vẫn nhiều hơn Lows (7)</p>
                        <p>→ Chưa xuất hiện sự bán tháo trên diện rộng</p>
                        <p>→ Thị trường chưa rơi vào trạng thái cực kỳ bi quan</p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>McClellan Summation Index</strong> ở mức +0</p>
                        <p>→ Động lượng breadth trung hạn ở trạng thái trung lập</p>
                        <p>→ Không có đà tăng hay giảm rõ rệt</p>
                    </div>
                    <div class="info-box warning">
                        <h4>Ý Nghĩa & Hành Động</h4>
                        <p>Tâm lý thị trường hiện tại <span class="danger">thận trọng đến tiêu cực</span></p>
                        <p>với lực bán chiếm ưu thế về độ rộng lẫn khối lượng.</p>
                        <p>Nhà đầu tư nên thận trọng và chờ đợi sự cải thiện về độ rộng tham gia</p>
                        <p>trước khi kỳ vọng một đợt tăng bền vững.</p>
                        <p><strong>Điều kiện sai:</strong></p>
                        <ol style="margin-left: 20px; line-height: 1.8;">
                            <li>Số mã tăng tăng đột biến trong khi TRIN vẫn trên 1 (nhiễu)</li>
                            <li>Thị trường trong trạng thái đi ngang (range-bound) khiến TRIN ít có ý nghĩa</li>
                            <li>Sự phân kỳ tích cực nếu VNINDEX tăng mạnh trong khi TRIN duy trì trên 1 (cảnh báo đà tăng không lành mạnh)</li>
                        </ol>
                    </div>
                `
            },
            {
                icon: "📜",
                title: "LỊCH SỬ & XU HƯỚNG BREADTH",
                content: `
                    <div class="info-box">
                        <h4>Kết Luận</h4>
                        <p>Breadth có dấu hiệu <span class="highlight">phục hồi mạnh mẽ ở ngắn hạn</span> sau một đợt suy yếu sâu,</p>
                        <p>nếu cấu trúc trung và dài hạn vẫn còn yếu, chưa thoát khỏi vùng tiêu cực.</p>
                    </div>
                    <div class="info-box">
                        <h4>Dẫn Chứng & Phân Tích</h4>
                        <p><strong>So với 1 tuần trước:</strong> percentile breadth đã cải thiện <span class="highlight">+7.0%</span></p>
                        <p><strong>So với 1 tháng trước:</strong> <span class="highlight">+2.1%</span></p>
                        <p>→ Cho thấy xu hướng đi lên gần đây</p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>Tuy nhiên:</strong> Mức percentile hiện tại (<span class="warning">25.4%</span>) vẫn nằm trong vùng thấp (dưới 30%) của 2 năm qua</p>
                    </div>
                    <div class="info-box">
                        <h4>Diễn Biến Chuỗi 20 Ngày Của MA Breadth</h4>
                        <p>Cho thấy một đợt phục hồi rõ rệt từ đáy:</p>
                        <p><strong>% mã trên MA5:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Đã tăng mạnh từ mức đáy <span class="danger">17.0%</span> (khoảng 13 phiên trước)</li>
                            <li>Lên <span class="highlight">48.1%</span> hiện tại</li>
                        </ul>
                        <p><strong>% trên MA20:</strong> Cũng phục hồi từ đáy 20.1% lên 35.8%</p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>NHƯNG:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>% trên MA20 đã giảm từ <span class="highlight">43.4%</span> xuống <span class="warning">35.8%</span></li>
                            <li>% trên MA200 giảm từ 55.0% xuống 46.6%</li>
                        </ul>
                        <p>→ Điều này cho thấy đà suy yếu vẫn chi phối khung trung đến dài hạn</p>
                        <p>→ Sự phục hồi gần đây chủ yếu là ngắn hạn</p>
                    </div>
                    <div class="info-box">
                        <h4>Ý Nghĩa & Hành Động</h4>
                        <p>Sự cải thiện trong vài phiên gần đây là <span class="highlight">tín hiệu tích cực</span></p>
                        <p>cho một đợt bật lại tiềm năng.</p>
                        <p><strong>Tuy nhiên:</strong> Để xác nhận một xu hướng tăng bền vững, cần thấy:</p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Sự cải thiện lan tỏa đến các khung trung hạn</li>
                            <li>Ví dụ: % trên MA20 vượt 50% và tiếp tục tăng</li>
                        </ul>
                        <p><span class="danger">Điều kiện sai:</span> Nếu % trên MA5 và MA20 không thể duy trì đà tăng mà quay đầu giảm trở lại</p>
                        <p>→ Xu hướng phục hồi ngắn hạn sẽ thất bại</p>
                        <p>→ Breadth có khả năng kiểm tra lại vùng đáy trước đó</p>
                    </div>
                `
            },
            {
                icon: "⚠️",
                title: "RỦI RO",
                content: `
                    <div class="info-box danger">
                        <h4>Ngắn Hạn (1-5 phiên)</h4>
                        <p><strong>Rủi ro: CAO</strong></p>
                        <p><strong>Lý do:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.8;">
                            <li>Đà tăng mạnh (thay đổi 5D +5.54%, RSI5=94.69 quá mua)</li>
                            <li>Tín hiệu mệt mỏi từ nến thân nhỏ</li>
                            <li>Sự suy yếu rõ rệt của market breadth:</li>
                            <ul style="margin-left: 20px;">
                                <li>Số mã giảm gấp đôi số mã tăng</li>
                                <li>TRIN=1.03, Volume Ratio=0.50x</li>
                            </ul>
                        </ul>
                        <p>→ Tạo ra nguy cơ điều chỉnh kỹ thuật mạnh</p>
                        <p><strong>Rủi ro lan tỏa sang trung hạn:</strong> <span class="warning">40-50%</span> nếu breadth không cải thiện</p>
                    </div>
                    <div class="info-box warning">
                        <h4>Trung Hạn (10-20 phiên)</h4>
                        <p><strong>Rủi ro: TRUNG BÌNH</strong></p>
                        <p><strong>Lý do:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.8;">
                            <li>Xu hướng tăng vẫn còn (giá trên MA20, Mom20=6.73)</li>
                            <li>Nhưng động lực từ độ rộng thị trường yếu:</li>
                            <ul style="margin-left: 20px;">
                                <li>Breadth percentile 25.4%</li>
                                <li>% mã trên MA20 giảm từ 43.4% xuống 35.8% trong 20 ngày</li>
                            </ul>
                        </ul>
                        <p>→ Khiến đà tăng dễ bị tổn thương</p>
                        <p>→ Xu hướng hiện tại có thể chưa bền vững</p>
                    </div>
                    <div class="info-box">
                        <h4>Dài Hạn (40-60 phiên)</h4>
                        <p><strong>Rủi ro: THẤP - TRUNG BÌNH</strong></p>
                        <p><strong>Lý do:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.8;">
                            <li>Xu hướng cơ bản vẫn tăng (giá cao hơn MA200, Mom200=33.22 dương mạnh)</li>
                            <li>Tuy nhiên:</li>
                            <ul style="margin-left: 20px;">
                                <li>Sự đồng thuận yếu từ khối lượng (thấp hơn VMA100)</li>
                                <li>Breadth trung-dài hạn chưa phục hồi (% mã trên MA200 giảm)</li>
                            </ul>
                        </ul>
                        <p>→ Là điểm yếu cần theo dõi</p>
                    </div>
                    <div class="info-box danger" style="border: 2px solid #ef4444;">
                        <h4>3 Điều Kiện Thất Bại Chính</h4>
                        <p>cho luận điểm "xu hướng tăng tiếp tục":</p>
                        <p><strong>1. Điều kiện về giá:</strong></p>
                        <p>Giá đóng cửa dưới MA5 (1,716) và sau đó là MA20 (1,708) một cách thuyết phục</p>
                        <p>đi kèm với ADX5 giảm mạnh từ mức 43.83</p>
                        <p>→ <span class="danger">Sẽ báo hiệu đảo chiều ngắn hạn</span></p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>2. Điều kiện về độ rộng (breadth):</strong></p>
                        <p>Các chỉ số breadth không cải thiện mà xấu đi hơn:</p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>% mã trên MA5 (hiện 48.1%) và MA20 (hiện 35.8%) quay đầu giảm trở lại</li>
                            <li>TRIN tăng vượt 1.5</li>
                            <li>Số mã tăng/giảm tiếp tục chênh lệch sâu</li>
                        </ul>
                        <p>→ Cho thấy áp lực bán lan rộng, đà tăng của chỉ số không có nền tảng</p>
                        <p>━━━━━━━━━━━━━━━━</p>
                        <p><strong>3. Điều kiện về khối lượng và động lượng:</strong></p>
                        <p>Khối lượng giao dịch giảm mạnh và duy trì dưới VMA20 (761.5 triệu)</p>
                        <p>đồng thời Mom5 (5.54) giảm nhanh so với Mom20 (6.73)</p>
                        <p>→ Xác nhận đà tăng ngắn hạn đã kiệt sức, không có dòng tiền hỗ trợ</p>
                    </div>
                `
            },
            {
                icon: "🎯",
                title: "KHUYẾN NGHỊ VỊ THẾ",
                alert: true,
                content: `
                    <p><strong>Hành động đề xuất:</strong> <span class="danger">Tạm đứng ngoài</span> hoặc <span class="warning">giảm tỷ trọng</span> (Take Partial Profit) đối với nhà đầu tư đang nắm giữ.</p>
                    <p><span class="danger">Không khuyến nghị mua mới</span> ở mức giá hiện tại.</p>
                    <p style="margin-top: 15px;"><strong>Bối cảnh:</strong></p>
                    <ul style="margin-left: 20px; line-height: 1.8;">
                        <li>Chỉ số ở vùng <span class="danger">quá mua cực độ</span> (RSI5=94.69)</li>
                        <li>Tiến sát kháng cự mạnh 1,778-1,780</li>
                        <li>Tâm lý và độ rộng thị trường lại bearish (breadth percentile chỉ 25.4%)</li>
                        <li>Sự phân kỳ này làm tăng rủi ro điều chỉnh</li>
                    </ul>
                    <p style="margin-top: 15px;"><strong>Hành động mua nên chờ:</strong> Giá điều chỉnh về các vùng hỗ trợ có độ tin cậy cao hơn (như MA20 1,708 hoặc POC 1,654) kèm theo sự cải thiện của breadth.</p>
                    <p style="margin-top: 15px;"><strong>Mức độ tự tin:</strong> <span class="highlight">7/10</span></p>
                    <p><strong>Lý do:</strong> Mức tin cậy cao dựa trên sự nhất quán giữa:</p>
                    <ul style="margin-left: 20px; line-height: 1.6;">
                        <li>Cảnh báo quá mua từ RSI</li>
                        <li>Kháng cự kỹ thuật</li>
                        <li>Tín hiệu bearish từ breadth</li>
                    </ul>
                    <p><strong>Nhưng:</strong> Động lượng trung hạn vẫn dương (Mom20=6.73) nên vẫn có 30% khả năng thị trường đi ngang để giảm nhiệt thay vì điều chỉnh sâu.</p>
                    <p style="margin-top: 15px;"><strong>Dẫn chứng:</strong></p>
                    <ul style="margin-left: 20px; line-height: 1.6;">
                        <li><strong>Từ Phân tích kỹ thuật:</strong> RSI5 = 94.69 (quá mua), giá tại 1,772 sát kháng cự 1,778-1,780</li>
                        <li><strong>Từ Phân tích Market Breadth:</strong> Số mã giảm (218) gần gấp đôi số mã tăng (113), TRIN=1.03, Volume Ratio=0.50x</li>
                        <li><strong>Từ Tóm tắt số liệu:</strong> Breadth percentile = 25.4% (vùng thấp)</li>
                    </ul>
                `
            },
            {
                icon: "🎯",
                title: "GIÁ MỤC TIÊU",
                content: `
                    <div class="info-box success">
                        <h4>Kịch Bản Tăng (Upside – Chốt lời/ Kháng cự)</h4>
                        <p><strong>1. 1,778 – 1,780:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Vùng kháng cự tức thì</li>
                            <li>Kết hợp đỉnh phiên và Band trên Bollinger 20</li>
                        </ul>
                        <p><strong>2. 1,804:</strong> Kháng cự tiếp theo, là Band trên Bollinger 5</p>
                    </div>
                    <div class="info-box">
                        <h4>Kịch Bản Giảm (Downside – Hỗ trợ/ Cắt lỗ)</h4>
                        <p><strong>1. 1,708 – 1,697:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Vùng hỗ trợ động quan trọng</li>
                            <li>Tương ứng với MA20 và MA10</li>
                            <li>Đây là mức thoái lui đầu tiên và hợp lý để tái lập vị thế mua nếu đà tăng trung hạn còn nguyên vẹn</li>
                        </ul>
                        <p><strong>2. 1,654 – 1,636:</strong></p>
                        <ul style="margin-left: 20px; line-height: 1.6;">
                            <li>Vùng hỗ trợ mạnh từ cấu trúc khối lượng</li>
                            <li>Bao gồm POC (1,654) và Band dưới Bollinger 20 (1,636)</li>
                            <li>Đây là vùng mua mạnh nếu xảy ra điều chỉnh sâu</li>
                        </ul>
                    </div>
                    <div class="info-box">
                        <h4>Dẫn Chứng</h4>
                        <p>Các mức giá này được trích trực tiếp từ mục "Mức Giá Quan Trọng" trong phân tích kỹ thuật.</p>
                        <p>Hỗ trợ MA20 (1,708) và POC (1,654) là các mức được nhấn mạnh có độ tin cậy cao.</p>
                    </div>
                `
            },
            {
                icon: "🎲",
                title: "KỊCH BẢN WHAT-IF (Phiên tiếp theo & 1-5 phiên)",
                content: `
                    <div class="info-box">
                        <h4>Kịch Bản 1 – Tích Cực (Breakout giả)</h4>
                        <p>Giá phá lên trên <span class="highlight">1,780</span> và đóng cửa trên mức này, với khối lượng vượt mức T-1 (980 triệu) và số mã tăng cải thiện rõ rệt (ví dụ: >150).</p>
                        <p>→ Động thái này sẽ tạm thời bác bỏ dấu hiệu quá mua, mở đường kiểm tra 1,804.</p>
                        <p><strong>Xác suất:</strong> <span class="highlight">[15–25%]</span></p>
                        <p><strong>Lý do:</strong> RSI quá mua cực độ và breadth yếu khiến khả năng breakout thật khó xảy ra ngay.</p>
                        <p><strong>Yếu tố quyết định:</strong> Khối lượng và sự hồi phục của độ rộng (số mã tăng, TRIN giảm dưới 1).</p>
                    </div>
                    <div class="info-box">
                        <h4>Kịch Bản 2 – Trung Tính (Đi ngang/Consolidation)</h4>
                        <p>Giá dao động trong phạm vi hẹp quanh mức hiện tại (ví dụ: 1,760 – 1,780), với nến tiếp tục có thân nhỏ và khối lượng giảm nhẹ.</p>
                        <p>→ Đây là kịch bản để giảm nhiệt RSI và chờ đợi thêm tín hiệu từ breadth.</p>
                        <p><strong>Xác suất:</strong> <span class="highlight">[40–50%]</span></p>
                        <p><strong>Lý do:</strong> Phù hợp với dấu hiệu do dự từ mô hình nến và cần thời gian để thị trường tiêu hóa đà tăng mạnh.</p>
                        <p><strong>Yếu tố quyết định:</strong> Phản ứng của giá tại vùng kháng cự 1,778-1,780 và hỗ trợ gần 1,765 (mở cửa phiên T-0).</p>
                    </div>
                    <div class="info-box warning">
                        <h4>Kịch Bản 3 – Tiêu Cực (Điều chỉnh bắt đầu)</h4>
                        <p>Giá giảm, đóng cửa dưới 1,765 và hướng về kiểm tra hỗ trợ MA10 (1,697) hoặc MA20 (1,708), đi kèm khối lượng lớn và breadth vẫn xấu (số mã giảm >250).</p>
                        <p>→ Đây sẽ là sự khởi đầu của đợt điều chỉnh kỹ thuật được cảnh báo.</p>
                        <p><strong>Xác suất:</strong> <span class="warning">[30–40%]</span></p>
                        <p><strong>Lý do:</strong> Sự kết hợp của RSI quá mua, breadth bearish và động lượng ngắn hạn có dấu hiệu chậm lại (Mom5 < Mom20) ủng hộ kịch bản này.</p>
                        <p><strong>Yếu tố quyết định:</strong> Việc giá có phá vỡ và đóng cửa dưới ngưỡng hỗ trợ tâm lý gần nhất.</p>
                    </div>
                    <div class="info-box danger">
                        <h4>Kịch Bản 4 – Black Swan (Đảo chiều mạnh)</h4>
                        <p>Giá giảm mạnh, phá vỡ ngay lập tức nhiều hỗ trợ (1,708, 1,697) với khối lượng cực lớn (>1.2 tỷ) và breadth cực kỳ xấu (TRIN >2, số mã giảm >300).</p>
                        <p>Kịch bản này xảy ra nếu áp lực bán trở nên hoảng loạn.</p>
                        <p><strong>Xác suất:</strong> <span class="danger">[5–10%]</span></p>
                        <p><strong>Lý do:</strong> Xác suất thấp do xu hướng trung hạn vẫn tăng và chưa có tín hiệu phân kỳ bearish rõ ràng từ RSI/ADX.</p>
                        <p><strong>Dấu hiệu cảnh báo sớm:</strong> Sự sụt giảm đột ngột của % mã trên MA5 từ mức 48.1% và CMF20 chuyển sang âm nhanh chóng.</p>
                    </div>
                `
            }
        ]
    }
};
