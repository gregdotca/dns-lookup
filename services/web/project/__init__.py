#!/usr/bin/env python3
import socket
from urllib.parse import quote

import dns.name
import dns.resolver
from flask import Flask, redirect, render_template, request
from markupsafe import escape

APP_TITLE = "DNS Lookup"
DEFAULT_DOMAIN = "example.com"
MISSING_TEXT = "*MISSING*"

dig_servers = {
    "Australia (Cloudflare)": "1.1.1.1",
    "Brazil (Claro)": "200.248.178.54",
    "Canada (Fortinet)": "208.91.112.53",
    "China (Aliyun)": "223.5.5.5",
    # "Netherlands (OpenTLD)": "80.80.80.80",
    # "Russia (IONICA)": "176.103.130.130",
    "South Africa (Liquid)": "5.11.11.5",
    # "Switzerland (Oskar Emmenegger)": "194.209.157.109",
    # "UK (Onyx)": "195.97.240.237",
    "USA (Google)": "8.8.8.8",
}

app = Flask(__name__, static_folder="assets")


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return render_template("home.html", app_title=APP_TITLE)
    else:
        # quote everything, including "/", so "/evil.com" can't become a
        # protocol-relative redirect to another site
        return redirect("/" + quote(request.form["domain"], safe=""))


@app.route("/<domain>", methods=["GET"])
def home_domain(domain):
    return process_domain(domain)


def process_domain(dom):
    results = ""

    domain_details = get_details(dom)
    ip_address = str(domain_details[0])
    ptr_record = str(domain_details[1])
    nameservers = str(domain_details[2])
    primary_a = str(domain_details[3])
    primary_mx = str(domain_details[4])
    primary_txt = str(domain_details[5])
    www_a = str(domain_details[6])
    mail_a = str(domain_details[7])

    if dom == "":
        return render_page(dom, "Enter a domain")

    # a domain can have several A records, so compare against all of them,
    # falling back to the system resolver's single address
    primary_ips = address_set(primary_a)
    expected_ips = primary_ips or address_set(ip_address)

    results += (
            "<strong>Domain Resolution:</strong> " + str(escape(dom)) + " -> " + str(escape(ip_address)) + "<BR><BR>"
    )
    results += (
            "<strong>PTR Resolution:</strong> "
            + str(escape(ip_address))
            + " -> "
            + highlight_text(ptr_record, get_colour(dom, ptr_record))
            + "<BR><BR>"
    )
    results += "<strong>DNS Servers:</strong> " + str(escape(nameservers)) + "<BR><BR>"
    results += "<strong>DNS Resolution (Primary A Record):</strong><BR><BR>"
    results += get_propagation(dom, dig_servers, expected_ips)
    results += "<BR><strong>Standard DNS Records:</strong><BR><BR>"
    results += (
            "<strong>Primary A:</strong> "
            + highlight_text(primary_a, "green" if primary_ips else "red")
            + "<BR>"
    )
    results += (
            "<strong>www. A:</strong> "
            + highlight_text(www_a, get_address_colour(expected_ips, address_set(www_a)))
            + "<BR>"
    )
    results += (
            "<strong>mail. A:</strong> "
            + highlight_text(mail_a, get_address_colour(expected_ips, address_set(mail_a)))
            + "<BR>"
    )
    results += (
            "<strong>MX:</strong> "
            + highlight_text(primary_mx, get_colour("10 mail." + dom, primary_mx))
            + "<BR>"
    )
    results += (
            "<strong>TXT:</strong> "
            + highlight_text(primary_txt, get_colour('"v=spf1 mx a -all"', primary_txt))
            + "<BR>"
    )
    return render_page(dom, results)


def render_page(dom, page_body):
    return render_template(
        "home.html", domain=dom, app_title=APP_TITLE, page_body=page_body
    )


def get_colour(source, target):
    return "green" if str(source) == str(target) else "red"


def address_set(text):
    return set() if text == MISSING_TEXT else set(text.split(", "))


def get_address_colour(expected, addresses):
    return "green" if addresses and addresses == expected else "red"


def highlight_text(text, colour):
    return (
            "<span style='font-weight: bold; color: var(--result-"
            + str(colour)
            + ")'>"
            + str(escape(str(text)))
            + "</span>"
    )


def get_details(dom):
    default_text = MISSING_TEXT

    try:
        ip = socket.gethostbyname(dom)
    except Exception:
        ip = default_text

    try:
        ptr = socket.getnameinfo((ip, 0), 0)[0]
    except Exception:
        ptr = default_text

    try:
        ns_raw = dns.resolver.resolve(dom, "NS")
        ns = ", ".join([str(x)[:-1] for x in ns_raw])
    except Exception:
        ns = default_text

    try:
        primary_a_raw = dns.resolver.resolve(dom, "A")
        primary_a = ", ".join([str(x) for x in primary_a_raw])
    except Exception:
        primary_a = default_text

    try:
        primary_mx_raw = dns.resolver.resolve(dom, "MX")
        primary_mx = ", ".join([format_mx(x) for x in primary_mx_raw])
    except Exception:
        primary_mx = default_text

    try:
        primary_txt_raw = dns.resolver.resolve(dom, "TXT")
        primary_txt = ", ".join([str(x) for x in primary_txt_raw])
    except Exception:
        primary_txt = default_text

    try:
        www_a_raw = dns.resolver.resolve("www." + dom, "A")
        www_a = ", ".join([str(x) for x in www_a_raw])
    except Exception:
        www_a = default_text

    try:
        mail_a_raw = dns.resolver.resolve("mail." + dom, "A")
        mail_a = ", ".join([str(x) for x in mail_a_raw])
    except Exception:
        mail_a = default_text

    return [ip, ptr, ns, primary_a, primary_mx, primary_txt, www_a, mail_a]


def format_mx(mx):
    # drop the final dot ("10 mail.example.com"), except on a null MX,
    # whose exchange is the root itself ("0 .")
    if mx.exchange == dns.name.root:
        return str(mx)
    return str(mx.preference) + " " + mx.exchange.to_text(omit_final_dot=True)


def get_propagation(dom, servers, expected_ips):
    default_text = "*FAILED*"

    try:
        results = ""
        resolver = dns.resolver.Resolver()
        # give up on a resolver after 2 seconds instead of dnspython's default 5
        resolver.lifetime = 2

        for key, value in servers.items():
            try:
                resolver.nameservers = [socket.gethostbyname(value)]
                for a_record in resolver.resolve(dom, "A"):
                    results += (
                            str(highlight_text(a_record, "green" if str(a_record) in expected_ips else "red"))
                            + "&nbsp;&nbsp;&nbsp;"
                    )
                results += key + "<BR>"

            except Exception:
                results += (
                        highlight_text(default_text, "red")
                        + "&nbsp;&nbsp;&nbsp;"
                        + key
                        + "<BR>"
                )

        return results

    except Exception:
        return highlight_text(default_text, "red")


if __name__ == "__main__":
    app.run()
