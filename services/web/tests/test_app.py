import dns.rdata
import dns.rdataclass
import dns.rdatatype
import pytest

import project

MISSING = project.MISSING_TEXT


@pytest.fixture
def client():
    return project.app.test_client()


def fake_details(monkeypatch, details):
    monkeypatch.setattr(project, "get_details", lambda dom: details)
    monkeypatch.setattr(project, "get_propagation", lambda dom, servers, expected_ips: "")


def mx(text):
    return dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.MX, text)


def test_format_mx_drops_final_dot():
    assert project.format_mx(mx("10 mail.example.com.")) == "10 mail.example.com"


def test_format_mx_keeps_null_mx():
    assert project.format_mx(mx("0 .")) == "0 ."


def test_highlight_text_escapes():
    html = project.highlight_text("<b>x</b>", "red")
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert "<b>" not in html


def test_address_set():
    assert project.address_set("192.0.2.1, 192.0.2.2") == {"192.0.2.1", "192.0.2.2"}
    assert project.address_set(MISSING) == set()


def test_get_address_colour():
    expected = {"192.0.2.1", "192.0.2.2"}
    assert project.get_address_colour(expected, {"192.0.2.2", "192.0.2.1"}) == "green"
    assert project.get_address_colour(expected, {"192.0.2.1"}) == "red"
    assert project.get_address_colour(set(), set()) == "red"


def test_post_quotes_domain_in_redirect(client):
    response = client.post("/", data={"domain": "/evil.com"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/%2Fevil.com"


def test_results_escape_domain(client, monkeypatch):
    fake_details(monkeypatch, [MISSING] * 8)
    body = client.get("/%3Cimg%20src=x%20onerror=alert(1)%3E").get_data(as_text=True)
    assert "&lt;img src=x onerror=alert(1)&gt;" in body
    assert "<img src=x" not in body


def test_results_inside_page(client, monkeypatch):
    fake_details(monkeypatch, [MISSING] * 8)
    body = client.get("/example.com").get_data(as_text=True)
    assert body.index("Domain Resolution") < body.index("</body>")
    assert body.rstrip().endswith("</html>")


def test_several_a_records_are_green(client, monkeypatch):
    fake_details(monkeypatch, [
        "192.0.2.1",
        "host.example.com",
        "ns1.example.com",
        "192.0.2.1, 192.0.2.2",
        "10 mail.example.com",
        '"v=spf1 mx a -all"',
        "192.0.2.2, 192.0.2.1",
        MISSING,
    ])
    body = client.get("/example.com").get_data(as_text=True)
    assert "var(--result-green)'>192.0.2.1, 192.0.2.2<" in body
    assert "var(--result-green)'>192.0.2.2, 192.0.2.1<" in body
    assert "var(--result-red)'>" + MISSING + "<" in body
    assert "var(--result-green)'>10 mail.example.com<" in body


def test_primary_a_green_without_system_resolver_ip(client, monkeypatch):
    # gethostbyname() can return a different address from a round-robin pool
    fake_details(monkeypatch, [
        "192.0.2.9",
        MISSING,
        MISSING,
        "192.0.2.1, 192.0.2.2",
        MISSING,
        MISSING,
        MISSING,
        MISSING,
    ])
    body = client.get("/example.com").get_data(as_text=True)
    assert "var(--result-green)'>192.0.2.1, 192.0.2.2<" in body


def test_propagation_marks_each_address(monkeypatch):
    class FakeResolver:
        def resolve(self, dom, record_type):
            return ["192.0.2.1", "192.0.2.9"]

    monkeypatch.setattr(project.dns.resolver, "Resolver", FakeResolver)
    html = project.get_propagation("example.com", {"Test": "192.0.2.53"}, {"192.0.2.1"})
    assert "var(--result-green)'>192.0.2.1<" in html
    assert "var(--result-red)'>192.0.2.9<" in html
    assert html.endswith("Test<BR>")
