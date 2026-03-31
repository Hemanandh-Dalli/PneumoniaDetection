import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Box,
  Stack,
} from "@mui/material";
import API, { buildAssetUrl } from "../api/api";
import Layout from "../components/Layout";

function Result() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state;

  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const predicted_class = state?.predicted_class;
  const confidence = state?.confidence;
  const chat_id = state?.chat_id;
  const image_path = state?.image_path;
  const heatmap_path = state?.heatmap_path;

  let severityLabel = "";
  let severityBg = "";
  let severityText = "";

  if (confidence < 0.6) {
    severityLabel = "Low Signal";
    severityBg = "rgba(62, 209, 164, 0.16)";
    severityText = "#71ebc4";
  } else if (confidence <= 0.8) {
    severityLabel = "Moderate Signal";
    severityBg = "rgba(255, 190, 92, 0.2)";
    severityText = "#ffd590";
  } else {
    severityLabel = "Strong Signal";
    severityBg = "rgba(255, 109, 118, 0.2)";
    severityText = "#ff9aa1";
  }

  useEffect(() => {
    if (!chat_id) return;

    const fetchChat = async () => {
      try {
        const res = await API.get(`/chat/${chat_id}`);
        setMessages(res.data.messages);
      } catch (err) {
        console.error("CHAT LOAD ERROR:", err);
      }
    };

    fetchChat();
  }, [chat_id]);

  const sendMessage = async () => {
    if (!newMessage.trim()) return;
    setLoading(true);

    try {
      const res = await API.post("/chat", {
        chat_id,
        message: newMessage,
      });

      setMessages((prev) => [
        ...prev,
        { role: "user", message: newMessage },
        { role: "ai", message: res.data.reply },
      ]);
      setNewMessage("");
    } catch (err) {
      console.error("CHAT ERROR:", err);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async () => {
    try {
      const res = await API.post(
        "/report",
        {
          predicted_class,
          confidence,
          explanation: messages
            .filter((m) => m.role === "ai" || m.role === "assistant")
            .map((m) => m.message)
            .join("\n\n"),
          image_path,
          heatmap_path: heatmap_path || "",
        },
        { responseType: "blob" }
      );

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "pneumonia_report.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("PDF ERROR:", err);
      alert("Failed to download report");
    }
  };

  if (!state || !predicted_class) {
    return (
      <Layout>
        <Container sx={{ mt: 4 }}>
          <Card className="glass-3d" sx={{ backgroundColor: "transparent", color: "#eff7ff" }}>
            <CardContent>
              <Typography variant="h6">
                No prediction data found. Please upload an X-ray again.
              </Typography>
              <Button
                sx={{
                  mt: 2,
                  borderRadius: 2.5,
                  background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
                }}
                variant="contained"
                onClick={() => navigate("/")}
              >
                Go to Upload
              </Button>
            </CardContent>
          </Card>
        </Container>
      </Layout>
    );
  }

  return (
    <Layout>
      <Container maxWidth="md" sx={{ mt: { xs: 2, md: 4 } }}>
        <Card className="glass-3d" sx={{ backgroundColor: "transparent", color: "#eff7ff" }}>
          <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
            <Typography className="page-title" gutterBottom>
              Prediction Result
            </Typography>

            <Typography className="page-subtitle" sx={{ mb: 2 }}>
              AI screening assessment, uploaded image review, and follow-up assistant in one panel.
            </Typography>

            {image_path && (
              <>
                <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                  Original X-ray
                </Typography>
                <img
                  src={buildAssetUrl(image_path)}
                  alt="Uploaded X-ray"
                  style={{
                    width: "100%",
                    borderRadius: "10px",
                    border: "1px solid rgba(163, 204, 255, 0.4)",
                  }}
                />
              </>
            )}

            {heatmap_path && (
              <>
                <Typography variant="subtitle1" sx={{ mt: 3, mb: 1 }}>
                  AI Focus View
                </Typography>
                <img
                  src={buildAssetUrl(heatmap_path)}
                  alt="Grad-CAM Heatmap"
                  style={{
                    width: "100%",
                    borderRadius: "10px",
                    border: "1px solid rgba(163, 204, 255, 0.4)",
                  }}
                />
              </>
            )}

            <Typography sx={{ mt: 3 }}>
              <strong>Diagnosis:</strong> {predicted_class}
            </Typography>

            <Typography sx={{ mt: 1 }}>
              <strong>Confidence:</strong> {(confidence * 100).toFixed(2)}%
            </Typography>

            <Box
              sx={{
                mt: 2,
                px: 1.5,
                py: 1,
                borderRadius: 2,
                backgroundColor: severityBg,
                color: severityText,
                border: "1px solid rgba(255, 255, 255, 0.14)",
                fontWeight: 700,
                width: "fit-content",
              }}
            >
              Severity Level: {severityLabel}
            </Box>

            <Typography className="section-title" sx={{ mt: 4 }}>
              Chat Assistant
            </Typography>

            <Box
              sx={{
                maxHeight: 260,
                overflowY: "auto",
                mt: 2,
                border: "1px solid rgba(163, 204, 255, 0.4)",
                borderRadius: 2,
                p: 1.5,
                background: "rgba(255, 255, 255, 0.03)",
              }}
            >
              {messages.map((msg, index) => (
                <Typography
                  key={index}
                  sx={{ mb: 1.5, textAlign: msg.role === "user" ? "right" : "left" }}
                >
                  <strong>{msg.role === "user" ? "You" : "AI"}:</strong> {msg.message}
                </Typography>
              ))}
            </Box>

            <TextField
              fullWidth
              multiline
              rows={2}
              sx={{ mt: 2 }}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Ask a follow-up question..."
            />

            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mt: 2 }}>
              <Button
                className="cta-btn"
                variant="contained"
                sx={{
                  background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
                }}
                onClick={sendMessage}
                disabled={loading}
              >
                {loading ? "Sending..." : "Send"}
              </Button>

              <Button
                className="cta-btn"
                variant="contained"
                sx={{
                  background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
                }}
                onClick={downloadReport}
              >
                Download Report (PDF)
              </Button>

              <Button
                className="cta-btn"
                variant="outlined"
                sx={{
                  borderColor: "rgba(163, 204, 255, 0.5)",
                  color: "#eff7ff",
                }}
                onClick={() => navigate("/")}
              >
                Upload Another Image
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Container>
    </Layout>
  );
}

export default Result;
